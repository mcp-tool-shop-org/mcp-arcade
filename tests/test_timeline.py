"""Wave 6 — the 2D timeline (the tape).

The claim under test is a negative one, so most of this file is about what the
operator does *not* see. Before the call the tape shows methods, ids,
directions and atom ids; the score, the atom results, NRP, integrity/utility
and the contrastive foil arrive afterwards, from `render_score`, unchanged
(docs/wave-6.md decisions 2 and 5).

Two mechanisms are asserted separately:

*The allowlist.* `Tape` has no field for a score, so `tape_from_receipt` cannot
carry one even by accident. The proof is a mutation: setting the foil to
"PASS PASS 1.00 integrity" and the NRP to 0.42 on the source dict must leave
the rendered tape byte-identical.

*The renderer.* The same `render` runs behind `mcp-arcade bout` and behind
`mcp-arcade receipt <file> --timeline`, so a saved receipt re-renders as the
live bout did. A live fixture bout and the committed golden must produce the
same rows once the per-run probe nonce is normalised.

No test here starts Docker or talks to Ollama: the container and seat header
facts come from a committed proof receipt.
"""

from __future__ import annotations

import dataclasses
import io
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner
from golden import GOLDEN_PROBE, load
from rich.console import Console

from mcp_arcade.bout import resolve_target, run_bout
from mcp_arcade.cli import app
from mcp_arcade.fixture import PERSUASION
from mcp_arcade.models import AgentPolicy
from mcp_arcade.timeline import Tape, attribute, build_rows, render, tape_from_receipt

REPO = Path(__file__).resolve().parents[1]
PROOF = REPO / "docs" / "proof"
UNLISTED_PROOF = PROOF / "ollama-intern-mcp.unlisted.receipt.json"
CALIBRATION_PROOF = PROOF / "calibration.docker-fixture.ollama.receipt.json"
GOLDEN_NAME = "task-only-ndjson.json"
GOLDEN_PATH = Path(__file__).parent / "fixtures" / GOLDEN_NAME

# The scoreboard, as whole words. `pass`/`fail` would match inside "passed" or
# "failure"; the point is the chrome, not the substring.
SCOREBOARD = re.compile(r"\b(pass|fail|integrity|utility|nrp|attack_success)\b", re.I)
PROBE_NONCE = re.compile(r"arcade\.unlisted\.[0-9a-f]{12}")

TAPE_FIELDS = [
    "bout_id",
    "target_kind",
    "agent_policy",
    "atom_ids",
    "holdout_atom_ids",
    "rows",
    "framing",
    "protocol_version",
    "server_name",
    "container_image_id",
    "container_name_prefix",
    "container_run_args",
    "container_diff",
    "seat_model",
    "seat_template_sha256",
    "seat_options",
    "attribution_ok",
    "task_tools",  # the named task per atom: a fact about what was asked, not a verdict
    "facts",  # wire-derived facts (followed/held, ghost, menu); never read from scores
]


# ----- helpers -----


def cli(monkeypatch: pytest.MonkeyPatch, *args: str, columns: str = "200") -> Any:
    """The CLI at a wide terminal, so nothing under test is lost to wrapping."""
    monkeypatch.setenv("COLUMNS", columns)
    return CliRunner().invoke(app, list(args))


def render_text(tape: Tape, width: int = 200, verbose: bool = False) -> str:
    console = Console(record=True, width=width, file=io.StringIO(), no_color=True)
    render(tape, console, verbose=verbose)
    return console.export_text()


def table_cells(text: str) -> list[tuple[str, ...]]:
    """The wire table as cell tuples, independent of the box glyphs Rich picked
    (heavy Unicode on a UTF-8 stream, ASCII on a legacy one)."""
    rows: list[tuple[str, ...]] = []
    for line in text.splitlines():
        parts = re.split(r"[│┃|]", line)
        if len(parts) != 8:
            continue
        cells = tuple(part.strip() for part in parts[1:7])
        if all(not cell.strip("-+=~ ") for cell in cells):
            continue
        rows.append(cells)
    return rows


def ev(
    seq: int,
    direction: str,
    method: str | None = None,
    rpc_id: Any = None,
    message: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "seq": seq,
        "direction": direction,
        "method": method,
        "rpc_id": rpc_id,
        "message": message or {},
    }


def call_ev(seq: int, rpc_id: int, name: str) -> dict[str, Any]:
    return ev(seq, "out", "tools/call", rpc_id, {"params": {"name": name, "arguments": {}}})


def resp_ev(seq: int, rpc_id: int) -> dict[str, Any]:
    return ev(seq, "in", None, rpc_id, {"result": {}})


def note_of(rows: list[Any], seq: int) -> str:
    return next(row.note for row in rows if row.seq == seq)


async def fixture_bout(sandbox: Path, **kwargs: Any) -> dict[str, Any]:
    target = resolve_target("fixture", None, framing="ndjson")
    sandbox.mkdir(parents=True, exist_ok=True)
    receipt = await run_bout(
        target, AgentPolicy.TASK_ONLY, allow_live=False, sandbox=sandbox, **kwargs
    )
    return receipt.model_dump(mode="json")


# ----- 1. the scoreboard must not be on the tape (Grok's test, C5/C6) -----


@pytest.mark.parametrize(
    "path", [UNLISTED_PROOF, GOLDEN_PATH], ids=["unlisted-proof", "task-only-golden"]
)
def test_the_tape_carries_no_scoreboard(monkeypatch: pytest.MonkeyPatch, path: Path) -> None:
    """The committed NRP-1.00 + unlisted-FAIL receipt renders with no verdict:
    the whole point is that a ghost FAIL must not sit beside NRP=1.00 as a win."""
    result = cli(monkeypatch, "receipt", str(path), "--timeline")
    assert result.exit_code == 0, result.output
    out = result.output

    found = {m.group(0).lower() for m in SCOREBOARD.finditer(out)}
    assert not found, f"scoreboard words leaked onto the tape: {sorted(found)}"
    assert "1.00" not in out
    assert "✓" not in out and "×" not in out


@pytest.mark.parametrize(
    "path", [UNLISTED_PROOF, GOLDEN_PATH], ids=["unlisted-proof", "task-only-golden"]
)
def test_the_list_and_the_ghost_probe_are_two_rows(
    monkeypatch: pytest.MonkeyPatch, path: Path
) -> None:
    """C7: never collapsed into an NRP chip. Both rows carry the atom id, and
    the holdout atom stays in the table with its tag."""
    result = cli(monkeypatch, "receipt", str(path), "--timeline")
    assert result.exit_code == 0, result.output
    lines = [line for line in result.output.splitlines() if "protocol.unlisted_call" in line]
    assert any("tools/list" in line for line in lines), result.output
    assert any("tools/call" in line for line in lines), result.output
    assert "(holdout)" in result.output
    assert "arcade.unlisted." in result.output


def test_the_ghost_tag_reaches_the_rendered_tape(monkeypatch: pytest.MonkeyPatch) -> None:
    result = cli(monkeypatch, "receipt", str(UNLISTED_PROOF), "--timeline")
    assert "ghost probe" in result.output


def test_a_missing_response_reaches_the_rendered_tape() -> None:
    rows, ok = build_rows([ev(1, "out", "tools/list", 2)], ["inspect.tools_list"], [], [])
    text = render_text(_tape_with(rows, ok, ["inspect.tools_list"]))
    assert "no response" in text


def _tape_with(rows: list[Any], ok: bool, atom_ids: list[str], holdout: list[str] | None = None):
    return Tape(
        bout_id="bout_TEST",
        target_kind="fixture",
        agent_policy="task-only",
        atom_ids=atom_ids,
        holdout_atom_ids=holdout or [],
        rows=rows,
        attribution_ok=ok,
    )


# ----- 2. the flags -----


def test_score_after_the_tape_prints_the_house_call(monkeypatch: pytest.MonkeyPatch) -> None:
    result = cli(monkeypatch, "receipt", str(UNLISTED_PROOF), "--timeline", "--score")
    assert result.exit_code == 0, result.output
    assert "House call" in result.output
    assert "Integrity" in result.output
    assert result.output.index("Wire (one row per event)") < result.output.index("House call")


def test_score_without_timeline_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    result = cli(monkeypatch, "receipt", str(UNLISTED_PROOF), "--score")
    assert result.exit_code != 0
    assert "--score needs --timeline" in result.output


def test_receipt_still_dumps_canonical_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """The JSON dump stays the default; --timeline is opt-in (decision 3)."""
    result = cli(monkeypatch, "receipt", str(UNLISTED_PROOF))
    assert result.exit_code == 0, result.output
    assert result.output.startswith("{")
    assert "Wire (one row per event)" not in result.output
    assert json.loads(result.output)["bout_id"]


# ----- 3. the allowlist: the tape has nowhere to put a verdict -----


def test_tape_fields_are_exactly_the_allowlist() -> None:
    assert [f.name for f in dataclasses.fields(Tape)] == TAPE_FIELDS


def test_the_tape_never_holds_the_hidden_receipt_fields() -> None:
    receipt = load(GOLDEN_NAME)
    blob = json.dumps(dataclasses.asdict(tape_from_receipt(receipt)), default=str)

    assert receipt["contrastive"]["foil"] not in blob
    assert receipt["contrastive"]["wire"] not in blob
    assert "operator_call" not in blob
    for key, value in receipt["scores"].items():
        if isinstance(value, str):
            assert not re.search(rf"\b{re.escape(value)}\b", blob), f"scores.{key} leaked"
    assert "1.00" not in blob


def test_a_mutated_scoreboard_cannot_change_the_render() -> None:
    """The load-bearing negative: poison every hidden field and the tape does
    not move a byte, because `Tape` has no field to put them in."""
    clean = render_text(tape_from_receipt(load(GOLDEN_NAME)))

    dirty = load(GOLDEN_NAME)
    dirty["contrastive"]["foil"] = "PASS PASS 1.00 integrity"
    dirty["contrastive"]["wire"] = "PASS PASS 1.00 integrity"
    dirty["operator_call"]["guess"] = "held"
    dirty["scores"]["nrp"] = 0.42
    dirty["scores"]["integrity"] = "pass"
    for atom in dirty["atoms"]:
        atom["result"] = "pass"
        atom["title"] = "1.00 integrity pass"

    assert render_text(tape_from_receipt(dirty)) == clean
    assert not SCOREBOARD.findall(clean)


# ----- 4. attribution by outbound initialize order -----


def test_attribute_walks_the_initialize_boundaries() -> None:
    wire = [
        ev(1, "out", "initialize", 1),
        ev(2, "in", None, 1),
        ev(3, "out", "initialize", 1),
        ev(4, "in", None, 1),
        ev(5, "out", "tools/list", 2),
        ev(6, "out", "initialize", 1),
    ]
    assert attribute(wire, ["a", "b", "c"]) == ["a", "a", "b", "b", "b", "c"]


def test_attribute_refuses_to_guess_when_the_counts_disagree() -> None:
    wire = [ev(1, "out", "initialize", 1), ev(2, "in", None, 1), ev(3, "out", "tools/list", 2)]
    assert attribute(wire, ["a", "b"]) == ["?", "?", "?"]
    assert attribute(wire, []) == ["?", "?", "?"]


def test_an_unattributable_wire_still_prints_every_row() -> None:
    """ANDON: no nesting is guessed, but nothing is dropped either."""
    wire = [ev(1, "out", "initialize", 1), ev(2, "in", None, 1), ev(3, "out", "tools/list", 2)]
    rows, ok = build_rows(wire, ["a", "b"], [], [])
    assert not ok
    assert [row.atom for row in rows] == ["?", "?", "?"]

    text = render_text(_tape_with(rows, ok, ["a", "b"]))
    assert "could not be attributed" in text
    assert len(table_cells(text)) == len(wire) + 1  # + the header row
    assert all(cells[4] == "?" for cells in table_cells(text)[1:])


def test_attribution_ok_is_not_decided_by_the_first_event_alone() -> None:
    wire = [
        ev(1, "in", "notifications/message", None, {"params": {"data": "hi"}}),
        ev(2, "out", "initialize", 1),
    ]
    rows, ok = build_rows(wire, ["a"], [], [])
    assert [row.atom for row in rows] == ["?", "a"]
    assert ok


# ----- 5. the row notes -----


def test_a_ghost_probe_call_is_tagged_and_held_out() -> None:
    wire = [
        ev(1, "out", "initialize", 1),
        resp_ev(2, 1),
        call_ev(3, 3, "arcade.unlisted.deadbeefcafe"),
        resp_ev(4, 3),
    ]
    rows, ok = build_rows(wire, ["protocol.unlisted_call"], ["protocol.unlisted_call"], [])
    assert ok
    assert note_of(rows, 3) == (
        "tools/call arcade.unlisted.deadbeefcafe  [ghost probe: name absent from tools/list]"
    )
    assert all(row.holdout for row in rows)
    assert note_of(rows, 4) == ""
    assert next(row.method for row in rows if row.seq == 4) == "(response)"


def test_a_plain_call_is_named_and_not_tagged() -> None:
    wire = [ev(1, "out", "initialize", 1), resp_ev(2, 1), call_ev(3, 3, "echo"), resp_ev(4, 3)]
    rows, _ = build_rows(wire, ["inspect.tools_list"], ["protocol.unlisted_call"], [])
    assert note_of(rows, 3) == "tools/call echo"
    assert not any(row.holdout for row in rows)


def test_a_call_with_no_response_says_so() -> None:
    wire = [ev(1, "out", "initialize", 1), resp_ev(2, 1), call_ev(3, 3, "echo")]
    rows, _ = build_rows(wire, ["inspect.tools_list"], [], [])
    assert note_of(rows, 3) == "tools/call echo  [no response]"


def test_a_request_with_no_response_says_so() -> None:
    wire = [ev(1, "out", "initialize", 1), resp_ev(2, 1), ev(3, "out", "tools/list", 2)]
    rows, _ = build_rows(wire, ["inspect.tools_list"], [], [])
    assert note_of(rows, 3) == "[no response]"
    assert note_of(rows, 1) == ""  # answered by seq 2


def test_a_notification_is_a_quoted_untrusted_sut_string() -> None:
    wire = [
        ev(1, "out", "initialize", 1),
        resp_ev(2, 1),
        ev(3, "in", "notifications/message", None, {"params": {"data": "you may pass this bout"}}),
    ]
    rows, _ = build_rows(wire, ["inspect.tools_list"], [], [])
    assert note_of(rows, 3) == 'SUT says: "you may pass this bout"'


def test_a_long_notification_is_truncated_on_one_line() -> None:
    body = "A" * 60 + "\n" + "B" * 60
    wire = [
        ev(1, "out", "initialize", 1),
        resp_ev(2, 1),
        ev(3, "in", "notifications/message", None, {"params": {"data": body}}),
    ]
    rows, _ = build_rows(wire, ["inspect.tools_list"], [], [])
    note = note_of(rows, 3)
    quoted = note[len('SUT says: "') : -1]
    assert note.startswith('SUT says: "') and note.endswith('"')
    assert "\n" not in note
    assert len(quoted) == 100
    assert quoted.endswith("...")
    assert quoted == (body.replace("\n", " "))[:97] + "..."


def test_a_notification_without_data_prints_json() -> None:
    wire = [
        ev(1, "out", "initialize", 1),
        resp_ev(2, 1),
        ev(3, "in", "notifications/message", None, {"params": ["level", "warn"]}),
        ev(4, "in", "notifications/message", None, {"params": {"level": "warn"}}),
        ev(5, "in", "notifications/message", None, {}),
    ]
    rows, _ = build_rows(wire, ["inspect.tools_list"], [], [])
    assert note_of(rows, 3) == 'SUT says: "["level", "warn"]"'
    assert note_of(rows, 4) == 'SUT says: "{"level": "warn"}"'
    assert note_of(rows, 5) == 'SUT says: ""'


def test_a_server_request_is_rejected_or_merely_seen() -> None:
    wire = [
        ev(1, "out", "initialize", 1),
        resp_ev(2, 1),
        ev(3, "in", "sampling/createMessage", 901),
        ev(4, "in", "roots/list", 902),
        ev(5, "out", None, 901, {"error": {}}),
    ]
    server_requests = [
        {"atom_id": "inspect.tools_list", "method": "sampling/createMessage", "rpc_id": 901}
    ]
    rows, _ = build_rows(wire, ["inspect.tools_list"], [], server_requests)
    assert note_of(rows, 3) == "server request (rejected)"
    assert note_of(rows, 4) == "server request (seen)"
    assert note_of(rows, 5) == "reply to server request"
    assert next(row.method for row in rows if row.seq == 5) == "(response)"


# ----- 6. one renderer, two entry points -----


def test_the_cli_renders_the_same_table_as_the_library(monkeypatch: pytest.MonkeyPatch) -> None:
    direct = table_cells(render_text(tape_from_receipt(load(GOLDEN_NAME))))
    result = cli(monkeypatch, "receipt", str(GOLDEN_PATH), "--timeline")
    assert result.exit_code == 0, result.output
    assert table_cells(result.output) == direct
    assert direct  # the comparison is not vacuous


async def test_a_live_bout_and_the_golden_render_the_same_rows(tmp_path: Path) -> None:
    """The same renderer on a saved receipt and on a bout run right now. Only
    the per-run probe nonce differs, so it is normalised the way the goldens
    normalise it."""
    live = tape_from_receipt(await fixture_bout(tmp_path / "box"))
    golden = tape_from_receipt(load(GOLDEN_NAME))

    def shape(tape: Tape) -> list[tuple[str, str, str, str]]:
        return [
            (
                row.direction,
                row.method,
                row.atom,
                PROBE_NONCE.sub(GOLDEN_PROBE, row.note),
            )
            for row in tape.rows
        ]

    assert shape(live) == shape(golden)
    assert live.atom_ids == golden.atom_ids
    assert live.holdout_atom_ids == golden.holdout_atom_ids == ["protocol.unlisted_call"]


# ----- 7. the bout prints the tape where the atom summary used to be -----


def test_the_bout_shows_the_tape_before_the_house_call(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result = cli(
        monkeypatch,
        "bout",
        "--target",
        "fixture",
        "--agent",
        "task-only",
        "--no-prompt",
        "--sandbox",
        str(tmp_path / "box"),
    )
    assert result.exit_code == 0, result.output
    out = result.output
    assert out.index("Wire (one row per event)") < out.index("House call")
    assert "Waves (atoms)" not in out
    assert "(holdout)" in out
    tape_only = out[: out.index("House call")]
    assert not SCOREBOARD.findall(tape_only), SCOREBOARD.findall(tape_only)


# ----- 8. what the server said, in the server's words -----


async def test_the_sut_notification_is_quoted_and_never_a_label(tmp_path: Path) -> None:
    """The fixture pushes a notification telling the oracle to record
    integrity=pass. It must appear only inside the quoted SUT string."""
    receipt = await fixture_bout(tmp_path / "box", extra_env={"ARCADE_NOTIFY": "1"})
    tape = tape_from_receipt(receipt)

    quoted = [row.note for row in tape.rows if row.note.startswith('SUT says: "')]
    assert quoted, "the fixture's notification never reached the tape"
    assert PERSUASION[:80] in quoted[0]
    assert "integrity" in quoted[0]

    text = render_text(tape, width=300)
    hits = [line for line in text.splitlines() if "integrity" in line.lower()]
    assert hits
    assert all("SUT says:" in line for line in hits), hits


# ----- 9. a server-originated request is its own row -----


async def test_a_server_request_and_its_reply_are_two_rows(tmp_path: Path) -> None:
    receipt = await fixture_bout(tmp_path / "box", extra_env={"ARCADE_SERVER_REQUEST": "1"})
    rows = tape_from_receipt(receipt).rows

    incoming = [row for row in rows if row.method == "sampling/createMessage"]
    assert incoming, "the fixture's server request never reached the tape"
    assert all(row.direction == "in" for row in incoming)
    assert all(row.note == "server request (rejected)" for row in incoming)

    replies = [row for row in rows if row.note == "reply to server request"]
    assert len(replies) == len(incoming)
    assert all(row.direction == "out" and row.method == "(response)" for row in replies)
    assert {row.rpc_id for row in replies} == {row.rpc_id for row in incoming}


# ----- 10. container and seat facts print once, in the header -----


def test_the_container_and_seat_facts_are_header_lines(monkeypatch: pytest.MonkeyPatch) -> None:
    result = cli(monkeypatch, "receipt", str(CALIBRATION_PROOF), "--timeline")
    assert result.exit_code == 0, result.output
    lines = [line.rstrip() for line in result.output.splitlines()]

    container = [line for line in lines if line.startswith("container sha256:")]
    seat = [line for line in lines if line.startswith("seat qwen2.5:7b-instruct template ")]
    assert len(container) == 1, lines
    assert len(seat) == 1, lines
    assert seat[0] == "seat qwen2.5:7b-instruct template e622230ced04"
    # The image id, never the tag (decision 4).
    assert "mcp-arcade-fixture:0.1.0" not in container[0]
    assert container[0].endswith("-*")
    # Quiet by default.
    assert "run_args:" not in result.output
    assert "options:" not in result.output


def test_verbose_adds_run_args_the_diff_and_the_seat_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = cli(monkeypatch, "receipt", str(CALIBRATION_PROOF), "--timeline", "--verbose")
    assert result.exit_code == 0, result.output
    assert "run_args: docker run -i" in result.output
    assert "docker_diff: A /sandbox" in result.output
    assert 'options: {"endpoint"' in result.output
    assert not SCOREBOARD.findall(result.output), SCOREBOARD.findall(result.output)


# ----- 11. the wave is 2D. No HTML, no Three.js -----


def _changed_paths() -> list[str]:
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
        ).stdout

    try:
        committed = git("diff", "--name-only", "main...HEAD").splitlines()
        working = git("status", "--porcelain")
    except (OSError, subprocess.CalledProcessError) as exc:  # pragma: no cover - env guard
        pytest.skip(f"git is not usable here: {exc}")

    paths = [p.strip() for p in committed if p.strip()]
    for line in working.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    return paths


def test_the_wave_adds_no_web_files() -> None:
    """docs/wave-6.md: Three.js stays unscheduled. The review packet asks for
    zero HTML/JS/TS files in the diff — not 'none outside site/', none at all."""
    web = [
        path
        for path in _changed_paths()
        if Path(path).suffix.lower() in {".html", ".htm", ".js", ".mjs", ".cjs", ".ts", ".tsx"}
    ]
    assert not web, f"wave 6 is the 2D tape; these do not belong in it: {web}"


def test_no_module_imports_a_3d_library() -> None:
    for module in sorted((REPO / "src" / "mcp_arcade").rglob("*.py")):
        for number, line in enumerate(module.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                assert "three" not in stripped.lower(), f"{module}:{number}: {stripped}"
