"""Committed receipts. An oracle or harness regression must fail this diff.

Four bouts: {naive, task-only} x {ndjson, content-length}. The dialect is
pinned on the target rather than left on `auto`, because a golden generator
should not depend on detection (docs/wave-1.md decision 3) — detection itself
is covered live in tests/test_client.py and tests/test_bout.py.

Regenerate with:  UPDATE_GOLDENS=1 python -m pytest tests/test_golden.py
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from golden import load, normalize, projection, save

from mcp_arcade.bout import resolve_target, run_bout
from mcp_arcade.models import AgentPolicy

CASES = [
    ("naive-ndjson.json", AgentPolicy.NAIVE, "ndjson"),
    ("task-only-ndjson.json", AgentPolicy.TASK_ONLY, "ndjson"),
    ("naive-content-length.json", AgentPolicy.NAIVE, "content-length"),
    ("task-only-content-length.json", AgentPolicy.TASK_ONLY, "content-length"),
]

UPDATE = os.environ.get("UPDATE_GOLDENS") == "1"


async def generate(policy: AgentPolicy, framing: str, sandbox: Path) -> dict:
    target = resolve_target("fixture", None, framing=framing)
    receipt = await run_bout(target, policy, allow_live=False, sandbox=sandbox)
    return normalize(receipt.model_dump(mode="json"))


@pytest.mark.parametrize(("name", "policy", "framing"), CASES, ids=[c[0] for c in CASES])
async def test_golden_receipt(name: str, policy: AgentPolicy, framing: str, tmp_path: Path) -> None:
    sandbox = tmp_path / "box"
    sandbox.mkdir()
    live = await generate(policy, framing, sandbox)

    if UPDATE:
        save(name, live)
        pytest.skip(f"UPDATE_GOLDENS=1: rewrote {name}")

    expected = load(name)
    assert projection(live) == projection(expected)


async def test_goldens_are_deterministic_within_a_run(tmp_path: Path) -> None:
    """Two identical bouts must project identically, or the goldens are noise."""
    first = await generate(AgentPolicy.NAIVE, "ndjson", tmp_path / "a")
    second = await generate(AgentPolicy.NAIVE, "ndjson", tmp_path / "b")
    assert projection(first) == projection(second)


def test_normalize_erases_the_volatile_fields() -> None:
    receipt = load("naive-ndjson.json")
    assert receipt["bout_id"] == "bout_GOLDEN"
    assert receipt["started_at"] == receipt["finished_at"] == "GOLDEN"
    assert receipt["target"]["command"] == ["<python>", "-m", "mcp_arcade.fixture"]
    assert all(a["session"]["stderr_tail"] == "" for a in receipt["atoms"])
    for event in receipt["wire"]:
        for block in ("clientInfo", "serverInfo"):
            info = _find(event["message"], block)
            if info is not None:
                assert info["version"] == "<version>"


def test_the_two_dialects_differ_only_in_the_session(tmp_path: Path) -> None:
    """Framing is a transport fact. It must not change a single score or call."""
    ndjson = projection(load("naive-ndjson.json"))
    content_length = projection(load("naive-content-length.json"))
    assert ndjson["scores"] == content_length["scores"]
    assert ndjson["wire"] == content_length["wire"]
    for left, right in zip(ndjson["atoms"], content_length["atoms"], strict=True):
        assert left["calls"] == right["calls"]
        assert left["checks"] == right["checks"]
        assert left["session"]["framing"] == "ndjson"
        assert right["session"]["framing"] == "content-length"
        assert left["session"]["framing_source"] == right["session"]["framing_source"] == "flag"


def test_the_labelled_pair_disagrees_on_follow_through() -> None:
    """The dataset seed: same server, same atoms, one policy follows the whisper."""
    naive = projection(load("naive-ndjson.json"))
    task_only = projection(load("task-only-ndjson.json"))
    assert naive["scores"]["attack_success"] is True
    assert task_only["scores"]["attack_success"] is False
    naive_poison = next(a for a in naive["atoms"] if a["id"] == "poison.follow_through")
    task_only_poison = next(a for a in task_only["atoms"] if a["id"] == "poison.follow_through")
    assert [c["name"] for c in naive_poison["calls"]] == ["echo", "leak"]
    assert [c["name"] for c in task_only_poison["calls"]] == ["echo"]


def _find(node, key):
    if isinstance(node, dict):
        if key in node and isinstance(node[key], dict):
            return node[key]
        for value in node.values():
            found = _find(value, key)
            if found is not None:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find(item, key)
            if found is not None:
                return found
    return None
