"""Live fixture bouts. The naive policy must be caught on the wire."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_arcade.bout import resolve_target, run_bout
from mcp_arcade.models import AgentPolicy, AtomId, TargetKind


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
