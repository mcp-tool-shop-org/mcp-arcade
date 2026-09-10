"""Dataset generator (wave 3). One JSONL row per atom, labels from the wire.

Reads bout receipts as raw JSON (not through the Pydantic model, so a future
atom id is routed to holdout instead of rejected), attributes the wire to
atoms by outbound `initialize` count, and writes:

  <out>/train.jsonl      rows from split=train receipts whose atom id is public
  <out>/holdout.jsonl    rows from split=holdout receipts, plus any row whose
                         atom id is not in PUBLIC_TRAIN_ATOM_IDS or is listed
                         in the receipt's holdout_atom_ids
  <out>/manifest.json    provenance, counts, drop tallies. File names only.

Never emitted: operator_call, contrastive, titles, hypothesis prose, check
detail text, stderr_tail, host paths. ERROR and SKIP atoms are dropped and
tallied; they are never rows. A receipt with split=proof yields zero rows.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from mcp_arcade import __version__
from mcp_arcade.models import SCHEMA_ID, ToolCall
from mcp_arcade.oracle import unauthorized_calls

# Frozen. Promoting a holdout atom to public-train is a reviewed code change here,
# never a re-run of the generator.
PUBLIC_TRAIN_ATOM_IDS: tuple[str, ...] = (
    "inspect.tools_list",
    "poison.follow_through",
    "temporal.rug_pull",
)

ROW_SCHEMA_ID = "mcp-arcade.row/v1"
_SEAT_FIELDS = ("model", "temperature", "seed", "num_ctx", "endpoint", "prompt_template_sha256")
_SPLITS = ("train", "holdout", "proof")


class DatasetError(RuntimeError):
    pass


@dataclass
class ReceiptReport:
    name: str
    sha256: str
    split: str
    rows_train: int = 0
    rows_holdout: int = 0
    dropped: Counter[str] = field(default_factory=Counter)
    reason: str | None = None  # whole-receipt drop reason


@dataclass
class Build:
    train: list[dict[str, Any]] = field(default_factory=list)
    holdout: list[dict[str, Any]] = field(default_factory=list)
    receipts: list[ReceiptReport] = field(default_factory=list)
    dropped: Counter[str] = field(default_factory=Counter)
    agent_policies: Counter[str] = field(default_factory=Counter)
    image_ids: set[str] = field(default_factory=set)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(receipt: dict[str, Any]) -> bytes:
    return (json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def _slice_wire(wire: list[dict[str, Any]], n_atoms: int) -> list[list[dict[str, Any]]] | None:
    """Split the flat wire into one slice per atom at each outbound initialize.
    None when the count does not match: never guess slices."""
    starts = [
        i
        for i, ev in enumerate(wire)
        if ev.get("direction") == "out" and ev.get("method") == "initialize"
    ]
    if len(starts) != n_atoms:
        return None
    bounds = starts + [len(wire)]
    return [wire[bounds[i] : bounds[i + 1]] for i in range(n_atoms)]


def _notifications(slice_: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        ev.get("message", {})
        for ev in slice_
        if ev.get("direction") == "in" and ev.get("method") and ev.get("rpc_id") is None
    ]


class AtomInvalid(ValueError):
    """A malformed atom. Tallied as a drop; never aborts the directory."""


def _attack_success(atom: dict[str, Any]) -> bool | None:
    if atom.get("id") != "poison.follow_through":
        return None
    try:
        calls = [ToolCall.model_validate(c) for c in atom.get("calls") or []]
    except (ValidationError, TypeError) as exc:
        raise AtomInvalid(f"malformed calls[]: {exc}") from exc
    return bool(unauthorized_calls(list(atom.get("authorized_tools") or []), calls))


def _session(atom: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    raw = atom.get("session") or {}
    seat_raw = raw.get("seat")
    seat = (
        {k: seat_raw.get(k) for k in _SEAT_FIELDS} if isinstance(seat_raw, dict) else None
    )  # allowlisted: a stray field on the receipt cannot become row text
    session = {
        k: raw.get(k)
        for k in (
            "framing",
            "framing_source",
            "protocol_version",
            "server_info",
            "server_capabilities",
        )
    }
    container = raw.get("container")
    if isinstance(container, dict):
        container = {
            k: container.get(k)
            for k in ("image", "image_id", "repo_digest", "fixture_image", "sandbox_method")
        }
    else:
        container = None
    session["seat"] = seat  # replay facts only; the seat never writes text here
    return session, container


def row_for(
    receipt: dict[str, Any],
    atom: dict[str, Any],
    wire_slice: list[dict[str, Any]],
    receipt_sha: str,
) -> dict[str, Any]:
    session, container = _session(atom)
    atom_id = str(atom.get("id"))
    return {
        "schema_id": ROW_SCHEMA_ID,
        "receipt_sha256": receipt_sha,
        "bout_id": receipt.get("bout_id"),
        "atom_id": atom_id,
        "agent_policy": receipt.get("agent_policy"),
        "task": atom.get("task"),
        "poison_source": atom.get("poison_source"),
        "authorized_tools": atom.get("authorized_tools") or [],
        "calls": atom.get("calls") or [],
        "tools_before": atom.get("tools_before") or [],
        "tools_after": atom.get("tools_after") or [],
        "env_before": atom.get("env_before") or {"files": {}},
        "env_after": atom.get("env_after") or {"files": {}},
        "notifications": _notifications(wire_slice),
        "server_requests": [
            {"method": r.get("method"), "rpc_id": r.get("rpc_id"), "rejected": r.get("rejected")}
            for r in receipt.get("server_requests") or []
            if r.get("atom_id") == atom_id
        ],
        "checks": [
            {"id": c.get("id"), "result": c.get("result")} for c in atom.get("checks") or []
        ],
        "session": session,
        "container": container,
        "labels": {
            "result": atom.get("result"),
            "attack_success": _attack_success(atom),
            "label_source": "wire",
        },
    }


def _validate(receipt: Any) -> str | None:
    if not isinstance(receipt, dict):
        return "invalid:not_an_object"
    if receipt.get("schema_id") != SCHEMA_ID:
        return "invalid:schema_id"
    if not isinstance(receipt.get("atoms"), list) or not receipt["atoms"]:
        return "invalid:no_atoms"
    if not isinstance(receipt.get("wire"), list):
        return "invalid:no_wire"
    split = (receipt.get("dataset") or {}).get("split")
    if split not in _SPLITS:
        return "invalid:split"
    return None


def ingest(path: Path, build: Build) -> ReceiptReport:
    raw = path.read_bytes()
    try:
        receipt = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        report = ReceiptReport(
            name=path.name, sha256=_sha256(raw), split="?", reason="invalid:json"
        )
        build.dropped[report.reason] += 1
        build.receipts.append(report)
        return report

    problem = _validate(receipt)
    split = (receipt.get("dataset") or {}).get("split", "?") if isinstance(receipt, dict) else "?"
    sha = _sha256(_canonical(receipt)) if isinstance(receipt, dict) else _sha256(raw)
    report = ReceiptReport(name=path.name, sha256=sha, split=str(split))
    build.receipts.append(report)
    if problem is not None:
        report.reason = problem
        build.dropped[problem] += 1
        return report

    if split == "proof":
        # Committed live traces are evidence, never training data.
        report.reason = "split:proof"
        build.dropped["split:proof"] += 1
        return report

    atoms = receipt["atoms"]
    slices = _slice_wire(receipt["wire"], len(atoms))
    if slices is None:
        report.reason = "wire_mismatch"
        build.dropped["wire_mismatch"] += 1
        return report

    holdout_ids = set((receipt.get("dataset") or {}).get("holdout_atom_ids") or [])
    policy = str(receipt.get("agent_policy"))
    for atom, wire_slice in zip(atoms, slices, strict=True):
        result = atom.get("result")
        if result == "error":
            report.dropped["atom:error"] += 1
            build.dropped["atom:error"] += 1
            continue
        if result == "skip":
            # Utility never earned. Not a "held" negative: that is the never-call cheat.
            report.dropped["atom:skip"] += 1
            build.dropped["atom:skip"] += 1
            continue
        try:
            row = row_for(receipt, atom, wire_slice, sha)
        except AtomInvalid:
            report.dropped["atom:invalid"] += 1
            build.dropped["atom:invalid"] += 1
            continue
        atom_id = row["atom_id"]
        to_holdout = (
            split == "holdout" or atom_id not in PUBLIC_TRAIN_ATOM_IDS or atom_id in holdout_ids
        )
        if to_holdout:
            build.holdout.append(row)
            report.rows_holdout += 1
        else:
            build.train.append(row)
            report.rows_train += 1
        build.agent_policies[policy] += 1
        if row["container"] and row["container"].get("image_id"):
            build.image_ids.add(str(row["container"]["image_id"]))
    return report


def discover(receipt_dir: Path) -> list[Path]:
    if not receipt_dir.is_dir():
        raise DatasetError(f"not a directory: {receipt_dir}")
    # A previous run's manifest inside the input tree is not a receipt.
    return sorted(
        p for p in receipt_dir.rglob("*.json") if p.is_file() and p.name != "manifest.json"
    )


def build(receipt_dir: Path) -> Build:
    out = Build()
    for path in discover(receipt_dir):
        ingest(path, out)
    return out


def _dumps_row(row: dict[str, Any]) -> str:
    return json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def manifest(result: Build) -> dict[str, Any]:
    return {
        "schema_id": "mcp-arcade.dataset/v1",
        "row_schema_id": ROW_SCHEMA_ID,
        "generator": {"name": "mcp-arcade", "version": __version__},
        "receipt_schema_id": SCHEMA_ID,
        "public_train_atom_ids": list(PUBLIC_TRAIN_ATOM_IDS),
        "label_source": "wire",
        "receipts": [
            {
                "name": r.name,
                "sha256": r.sha256,
                "split": r.split,
                "rows_train": r.rows_train,
                "rows_holdout": r.rows_holdout,
                "dropped": dict(sorted(r.dropped.items())),
                "reason": r.reason,
            }
            for r in sorted(result.receipts, key=lambda r: r.name)
        ],
        "rows": {"train": len(result.train), "holdout": len(result.holdout)},
        "dropped": dict(sorted(result.dropped.items())),
        "agent_policies": dict(sorted(result.agent_policies.items())),
        "docker_image_ids": sorted(result.image_ids),
        "never_carried": [
            "operator_call",
            "contrastive",
            "tui",
            "hypothesis",
            "check.detail",
            "stderr_tail",
            "host_paths",
        ],
    }


def write(result: Build, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows_train = sorted(result.train, key=lambda r: (r["receipt_sha256"], r["atom_id"]))
    rows_holdout = sorted(result.holdout, key=lambda r: (r["receipt_sha256"], r["atom_id"]))
    (out_dir / "train.jsonl").write_text(
        "".join(_dumps_row(r) + "\n" for r in rows_train), encoding="utf-8"
    )
    (out_dir / "holdout.jsonl").write_text(
        "".join(_dumps_row(r) + "\n" for r in rows_holdout), encoding="utf-8"
    )
    man = manifest(result)
    (out_dir / "manifest.json").write_text(
        json.dumps(man, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return man
