"""The 2D timeline (wave 6): the tape, one row per wire event, receipt-first.

This is the operator's diagnostic surface (C7). It is built from a `Tape`,
an allowlisted view of the receipt that has no fields for scores, atom
results, `operator_call` or `contrastive`, so the renderer cannot show a
verdict before the operator calls it (C5). No bar, no colour by result, no
check marks. Holdout atoms stay in the table with a dim tag.

Events are attributed to atoms by outbound `initialize` order, the same rule
the dataset uses. Nothing is folded under a tools/call: notifications,
server-originated requests, the ghost probe and a request that never got a
response are each their own row or row note.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.text import Text

from mcp_arcade.atoms.unlisted import PROBE_PREFIX

_ATTRIBUTION_UNKNOWN = "?"


@dataclass(frozen=True)
class TapeRow:
    seq: int
    direction: str
    method: str
    rpc_id: str
    atom: str
    holdout: bool
    note: str


@dataclass
class Tape:
    """Everything the timeline may see. Nothing else exists on this type."""

    bout_id: str
    target_kind: str
    agent_policy: str
    atom_ids: list[str]
    holdout_atom_ids: list[str]
    rows: list[TapeRow]
    framing: str | None = None
    protocol_version: str | None = None
    server_name: str | None = None
    container_image_id: str | None = None
    container_name_prefix: str | None = None
    container_run_args: list[str] = field(default_factory=list)
    container_diff: list[str] = field(default_factory=list)
    seat_model: str | None = None
    seat_template_sha256: str | None = None
    seat_options: dict[str, Any] = field(default_factory=dict)
    attribution_ok: bool = True


def initialize_count_matches(wire: list[dict[str, Any]], atom_ids: list[str]) -> bool:
    starts = sum(
        1 for ev in wire if ev.get("direction") == "out" and ev.get("method") == "initialize"
    )
    return starts == len(atom_ids)


def attribute(wire: list[dict[str, Any]], atom_ids: list[str]) -> list[str]:
    """Atom id per wire event by outbound initialize order. If the count of
    initialize events does not match the atom count, every event is `?`:
    the timeline never guesses a nest. An event before the first initialize
    (a server that talks first) is `?` on its own; that is not a mismatch."""
    starts = [
        i
        for i, ev in enumerate(wire)
        if ev.get("direction") == "out" and ev.get("method") == "initialize"
    ]
    if len(starts) != len(atom_ids):
        return [_ATTRIBUTION_UNKNOWN] * len(wire)
    out: list[str] = []
    current = _ATTRIBUTION_UNKNOWN
    k = 0
    for i in range(len(wire)):
        if k < len(starts) and i == starts[k]:
            current = atom_ids[k]
            k += 1
        out.append(current)
    return out


def _fmt_id(value: Any) -> str:
    return "" if value is None else str(value)


def _quoted_sut(params: Any) -> str:
    """Notification payload as a quoted, untrusted SUT string. Never a label."""
    if isinstance(params, dict) and "data" in params:
        body = params["data"]
        text = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
    else:
        text = json.dumps(params, ensure_ascii=False) if params is not None else ""
    text = text.replace("\n", " ")
    if len(text) > 100:
        text = text[:97] + "..."
    return f'SUT says: "{text}"'


def build_rows(
    wire: list[dict[str, Any]],
    atom_ids: list[str],
    holdout_atom_ids: list[str],
    server_requests: list[dict[str, Any]],
) -> tuple[list[TapeRow], bool]:
    atoms = attribute(wire, atom_ids)
    ok = initialize_count_matches(wire, atom_ids)
    holdout = set(holdout_atom_ids)
    server_req_ids = {(_fmt_id(r.get("rpc_id")), r.get("method")) for r in server_requests}
    answered: set[str] = {
        _fmt_id(ev.get("rpc_id"))
        for ev in wire
        if ev.get("direction") == "in" and ev.get("method") is None and ev.get("rpc_id") is not None
    }
    rows: list[TapeRow] = []
    for ev, atom in zip(wire, atoms, strict=True):
        direction = str(ev.get("direction") or "")
        method = ev.get("method")
        rpc_id = _fmt_id(ev.get("rpc_id"))
        message = ev.get("message") or {}
        note = ""
        if direction == "out" and method == "tools/call":
            params = message.get("params") or {}
            name = str(params.get("name") or "")
            note = f"tools/call {name}"
            if name.startswith(PROBE_PREFIX):
                note += "  [ghost probe: name absent from tools/list]"
            if rpc_id and rpc_id not in answered:
                note += "  [no response]"
        elif direction == "out" and method and rpc_id and rpc_id not in answered:
            note = "[no response]"
        elif direction == "in" and method and not rpc_id:
            note = _quoted_sut(message.get("params"))
        elif direction == "in" and method and rpc_id:
            tag = "rejected" if (rpc_id, method) in server_req_ids else "seen"
            note = f"server request ({tag})"
        elif direction == "out" and method is None and rpc_id:
            note = "reply to server request"
        rows.append(
            TapeRow(
                seq=int(ev.get("seq") or 0),
                direction=direction,
                method=str(method or "(response)"),
                rpc_id=rpc_id,
                atom=atom,
                holdout=atom in holdout,
                note=note,
            )
        )
    return rows, ok


def tape_from_receipt(receipt: dict[str, Any]) -> Tape:
    """The allowlist. Reads wire, server_requests, atom order, holdout ids and
    header session facts. Does not read scores, atom results, checks,
    operator_call or contrastive: there is no field on Tape to put them in."""
    atoms = receipt.get("atoms") or []
    atom_ids = [str(a.get("id")) for a in atoms]
    dataset = receipt.get("dataset") or {}
    holdout = [str(x) for x in dataset.get("holdout_atom_ids") or []]
    rows, ok = build_rows(
        receipt.get("wire") or [], atom_ids, holdout, receipt.get("server_requests") or []
    )
    tape = Tape(
        bout_id=str(receipt.get("bout_id") or ""),
        target_kind=str((receipt.get("target") or {}).get("kind") or ""),
        agent_policy=str(receipt.get("agent_policy") or ""),
        atom_ids=atom_ids,
        holdout_atom_ids=holdout,
        rows=rows,
        attribution_ok=ok,
    )
    sessions = [a.get("session") or {} for a in atoms]
    first = next(
        (s for s in sessions if s.get("protocol_version")), sessions[0] if sessions else {}
    )
    tape.framing = first.get("framing")
    tape.protocol_version = first.get("protocol_version")
    info = first.get("server_info") or {}
    tape.server_name = str(info.get("name")) if info.get("name") else None
    container = next((s.get("container") for s in sessions if s.get("container")), None)
    if isinstance(container, dict):
        tape.container_image_id = str(container.get("image_id") or "")
        name = str(container.get("name") or "")
        tape.container_name_prefix = name.rsplit("-", 1)[0] + "-*" if name else None
        tape.container_run_args = [str(x) for x in container.get("run_args") or []]
        tape.container_diff = [str(x) for x in container.get("docker_diff") or []]
    seat = next((s.get("seat") for s in sessions if s.get("seat")), None)
    if isinstance(seat, dict):
        tape.seat_model = str(seat.get("model") or "")
        tape.seat_template_sha256 = str(seat.get("prompt_template_sha256") or "")
        tape.seat_options = {
            k: seat.get(k) for k in ("temperature", "seed", "num_ctx", "endpoint") if k in seat
        }
    return tape


def render(tape: Tape, console: Console, verbose: bool = False) -> None:
    """The tape. No score, no colour by result, no check marks."""
    header = (
        f"Tape [cyan]{tape.bout_id}[/cyan]  target={tape.target_kind}  policy={tape.agent_policy}"
    )
    if tape.framing or tape.protocol_version:
        header += f"  framing={tape.framing or '?'}  protocol={tape.protocol_version or '?'}"
    if tape.server_name:
        header += f"  server={tape.server_name}"
    console.print(header)
    if tape.container_image_id:
        console.print(
            f"container {tape.container_image_id[:19]} {tape.container_name_prefix or ''}".rstrip()
        )
        if verbose:
            console.print("  run_args: " + " ".join(tape.container_run_args))
            console.print("  docker_diff: " + (", ".join(tape.container_diff) or "(none)"))
    if tape.seat_model:
        console.print(f"seat {tape.seat_model} template {(tape.seat_template_sha256 or '')[:12]}")
        if verbose:
            console.print("  options: " + json.dumps(tape.seat_options, sort_keys=True))
    if not tape.attribution_ok:
        console.print(
            "[dim]wire could not be attributed to atoms (initialize count differs); "
            "atom column is ?[/dim]"
        )

    table = Table(title="Wire (one row per event)", show_header=True)
    table.add_column("seq", justify="right")
    table.add_column("dir")
    table.add_column("method")
    table.add_column("id", justify="right")
    table.add_column("atom")
    table.add_column("note", overflow="fold")
    for row in tape.rows:
        atom = row.atom
        if row.holdout:
            atom = f"[dim]{atom} (holdout)[/dim]"
        table.add_row(
            str(row.seq),
            Text(row.direction),
            Text(row.method),
            Text(row.rpc_id),
            atom,
            Text(row.note),  # plain text: "[ghost probe ...]" is not Rich markup
        )
    console.print(table)
    console.print()
