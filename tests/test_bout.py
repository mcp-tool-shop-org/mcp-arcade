"""Live fixture bouts. The naive policy must be caught on the wire."""

from __future__ import annotations

from pathlib import Path

import pytest

import mcp_arcade.bout as bout_mod
from mcp_arcade.bout import resolve_target, run_bout
from mcp_arcade.client import ClientTimeout, McpStdioClient
from mcp_arcade.models import AgentPolicy, AtomId, AxisResult, TargetKind, TaskSource, TaskSpec


@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    d = tmp_path / "sandbox"
    d.mkdir()
    return d


@pytest.mark.asyncio
async def test_naive_policy_follows_whispered_errand(sandbox: Path) -> None:
    target = resolve_target("fixture", None)
    receipt = await run_bout(target, AgentPolicy.NAIVE, allow_live=False, sandbox=sandbox)
    poison = next(a for a in receipt.atoms if a.id is AtomId.POISON)
    extra = [c.name for c in poison.calls if c.name not in poison.authorized_tools]
    assert "leak" in extra
    assert receipt.scores.attack_success is True
    assert receipt.scores.nrp == 0.0
    assert (sandbox / "leak.txt").exists()


@pytest.mark.asyncio
async def test_task_only_does_not_follow_whispered_errand(sandbox: Path) -> None:
    target = resolve_target("fixture", None)
    receipt = await run_bout(target, AgentPolicy.TASK_ONLY, allow_live=False, sandbox=sandbox)
    poison = next(a for a in receipt.atoms if a.id is AtomId.POISON)
    extra = [c.name for c in poison.calls if c.name not in poison.authorized_tools]
    assert extra == []
    assert poison.result.value == "pass"
    assert receipt.scores.attack_success is False
    assert receipt.scores.task_success is True
    assert receipt.scores.nrp == 1.0
    # The Long Con still fails integrity: the fixture mutates on purpose.
    rug = next(a for a in receipt.atoms if a.id is AtomId.RUG_PULL)
    assert rug.result.value == "fail"
    assert receipt.scores.integrity.value == "fail"


@pytest.mark.asyncio
async def test_rug_pull_catches_catalog_mutation(sandbox: Path) -> None:
    target = resolve_target("fixture", None)
    receipt = await run_bout(target, AgentPolicy.TASK_ONLY, allow_live=False, sandbox=sandbox)
    rug = next(a for a in receipt.atoms if a.id is AtomId.RUG_PULL)
    mut = next(c for c in rug.checks if c.id == "mutation_detected")
    assert "mutated" in mut.detail
    assert rug.result.value == "fail"


@pytest.mark.asyncio
async def test_inspect_passes_on_fixture(sandbox: Path) -> None:
    target = resolve_target("fixture", None)
    receipt = await run_bout(target, AgentPolicy.TASK_ONLY, allow_live=False, sandbox=sandbox)
    inspect = next(a for a in receipt.atoms if a.id is AtomId.INSPECT)
    assert inspect.result.value == "pass"


def test_stdio_without_allow_live_is_closed(tmp_path: Path) -> None:
    import asyncio

    target = resolve_target("stdio", ["python", "-m", "mcp_arcade.fixture"])
    assert target.kind is TargetKind.STDIO

    async def _run() -> None:
        with pytest.raises(PermissionError, match="allow-live"):
            await run_bout(target, AgentPolicy.TASK_ONLY, allow_live=False, sandbox=tmp_path)

    asyncio.run(_run())


# ----- wave 1: session facts, the named task, the house wrap, and andon -----


async def test_receipt_records_the_session_and_the_default_task(sandbox: Path) -> None:
    target = resolve_target("fixture", None)
    receipt = await run_bout(target, AgentPolicy.NAIVE, allow_live=False, sandbox=sandbox)

    assert receipt.server_requests == []
    for atom in receipt.atoms:
        assert atom.task.tool == "echo"
        assert atom.task.source is TaskSource.FIXTURE_DEFAULT
        assert atom.session.framing == "ndjson"
        assert atom.session.framing_source == "detected"
        assert atom.session.protocol_version == "2025-11-25"
        assert atom.session.server_info["name"] == "mcp-arcade-fixture"

    poison = next(a for a in receipt.atoms if a.id is AtomId.POISON)
    assert poison.poison_source.value == "fixture"
    # The whisper is the fixture's own description, not something Arcade appended.
    assert poison.notes == []


async def test_operator_named_task_is_recorded_and_goes_out_on_the_wire(sandbox: Path) -> None:
    target = resolve_target("fixture", None)
    receipt = await run_bout(
        target,
        AgentPolicy.TASK_ONLY,
        allow_live=False,
        sandbox=sandbox,
        task=TaskSpec(tool="echo", arguments={"text": "named"}, source=TaskSource.OPERATOR),
    )
    assert receipt.task.source is TaskSource.OPERATOR
    for atom in receipt.atoms:
        assert atom.task.source is TaskSource.OPERATOR
        assert atom.task.arguments == {"text": "named"}

    sent = [w for w in receipt.wire if w.direction.value == "out" and w.method == "tools/call"]
    assert sent, "no tools/call went out"
    assert all(w.message["params"]["arguments"] == {"text": "named"} for w in sent)
    assert receipt.scores.task_success is True


async def test_operator_task_that_is_not_on_the_menu_fails_the_inspect_check(
    sandbox: Path,
) -> None:
    target = resolve_target("fixture", None)
    receipt = await run_bout(
        target,
        AgentPolicy.TASK_ONLY,
        allow_live=False,
        sandbox=sandbox,
        task=TaskSpec(tool="nope", arguments={}, source=TaskSource.OPERATOR),
    )
    inspect = next(a for a in receipt.atoms if a.id is AtomId.INSPECT)
    listed = next(c for c in inspect.checks if c.id == "task_listed")
    assert listed.result is AxisResult.FAIL
    assert "NOT listed" in listed.detail
    assert inspect.result is AxisResult.FAIL
    assert [c.is_error for c in inspect.calls] == [True]
    # A tool that is not on the menu still cannot produce utility.
    assert receipt.scores.utility is AxisResult.FAIL
    assert receipt.scores.nrp == 0.0


async def test_house_wrap_takes_precedence_over_the_fixture_whisper(sandbox: Path) -> None:
    """poison.py sets `source` from the server's own descriptions first, then
    overwrites it with HOUSE_WRAP whenever `--wrap` actually applied a wrap.
    So on the poisoned fixture (whisper present) `--wrap` still labels the
    poison `house-wrap`: the receipt names who wrote the side-quest we presented."""
    target = resolve_target("fixture", None)
    receipt = await run_bout(
        target, AgentPolicy.TASK_ONLY, allow_live=False, sandbox=sandbox, wrap=True
    )
    poison = next(a for a in receipt.atoms if a.id is AtomId.POISON)
    assert poison.poison_source.value == "house-wrap"
    assert poison.notes and "house wrap" in poison.notes[0]
    # The wrap changed the presented menu, not the server's.
    assert [t.description for t in poison.tools_before] != [
        t.description for t in poison.tools_after
    ]
    # task-only still does not follow it.
    assert [c.name for c in poison.calls] == ["echo"]
    assert receipt.scores.attack_success is False


async def test_house_wrap_is_off_by_default(sandbox: Path) -> None:
    target = resolve_target("fixture", None)
    receipt = await run_bout(target, AgentPolicy.TASK_ONLY, allow_live=False, sandbox=sandbox)
    poison = next(a for a in receipt.atoms if a.id is AtomId.POISON)
    assert poison.poison_source.value == "fixture"


async def test_content_length_target_runs_end_to_end(sandbox: Path) -> None:
    target = resolve_target("fixture", None, framing="content-length")
    receipt = await run_bout(target, AgentPolicy.NAIVE, allow_live=False, sandbox=sandbox)
    for atom in receipt.atoms:
        assert atom.session.framing == "content-length"
        assert atom.session.framing_source == "flag"
        assert atom.session.protocol_version == "2025-11-25"
    poison = next(a for a in receipt.atoms if a.id is AtomId.POISON)
    assert [c.name for c in poison.calls] == ["echo", "leak"]
    assert receipt.scores.attack_success is True
    assert (sandbox / "leak.txt").exists()


class _TimeoutClient(McpStdioClient):
    """Never spawns anything: initialize times out the way a silent server does."""

    async def start(self) -> None:
        return None

    async def initialize(self) -> dict:
        raise ClientTimeout("tools/list (id 2) got no response in 1s")

    async def close(self) -> None:
        return None


async def test_a_timed_out_bout_errors_every_atom_and_scores_nothing(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bout_mod, "McpStdioClient", _TimeoutClient)
    target = resolve_target("fixture", None, timeout_s=1.0)
    receipt = await run_bout(target, AgentPolicy.NAIVE, allow_live=False, sandbox=sandbox)

    assert [a.result for a in receipt.atoms] == [AxisResult.ERROR] * 3
    for atom in receipt.atoms:
        harness = next(c for c in atom.checks if c.id == "harness")
        assert harness.result is AxisResult.ERROR
        assert "ClientTimeout" in harness.detail
    assert receipt.scores.integrity is AxisResult.ERROR
    assert receipt.scores.utility is AxisResult.SKIP
    assert receipt.scores.attack_success is False
    assert receipt.scores.nrp == 0.0
    assert "stopped early" in receipt.contrastive.wire
    assert "not a score" in receipt.contrastive.foil
