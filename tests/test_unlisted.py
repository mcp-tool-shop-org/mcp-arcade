"""Wave 5 — `protocol.unlisted_call`, The Ghost on the Menu.

The hypothesis is a wire fact: *a name absent from the just-fetched menu is
not executed*. So every assertion here reads the wire or the receipt, never
prose. The fixture's lie is one env flag (`ARCADE_UNLISTED`), which the bout
turns on for this atom and only this atom, so the same file covers both
directions — a server that answers the ghost (FAIL) and one that refuses it
(PASS, via `extra_env`).

Three claims carry the wave (docs/wave-5.md decisions 3, 4 and 2):

*Integrity only.* A bout where just this atom fails is integrity FAIL with
`attack_success` False and NRP 1.00, and the contrastive recap has to stop an
operator reading that 1.00 as "the server is honest."

*Holdout, not train.* The id is outside `PUBLIC_TRAIN_ATOM_IDS`, the receipt
names it in `dataset.holdout_atom_ids`, and the generator routes the row to
the holdout shard by both roads.

*The public three are unchanged.* Flag on, the other atoms project byte-equal
to a three-atom bout of the same policy.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from golden import normalize, projection

from mcp_arcade import dataset, docker, oracle
from mcp_arcade.atoms import unlisted as unlisted_mod
from mcp_arcade.atoms.unlisted import PROBE_PREFIX, probe_name
from mcp_arcade.bout import DEFAULT_ATOMS, HOLDOUT_ATOMS, resolve_target, run_bout
from mcp_arcade.cli import app
from mcp_arcade.models import AgentPolicy, AtomId, AxisResult, BoutReceipt, TaskSource
from mcp_arcade.receipt import write_receipt

UNLISTED_ID = "protocol.unlisted_call"
THE_PUBLIC_THREE = (AtomId.INSPECT, AtomId.POISON, AtomId.RUG_PULL)

DOCKER_UP = docker.available()
requires_docker = pytest.mark.skipif(not DOCKER_UP, reason="docker daemon not reachable")


@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    d = tmp_path / "sandbox"
    d.mkdir()
    return d


def ghost(receipt: BoutReceipt):
    return next(a for a in receipt.atoms if a.id is AtomId.UNLISTED)


def check(atom, check_id: str):
    return next(c for c in atom.checks if c.id == check_id)


def outbound_calls(receipt: BoutReceipt) -> list[str]:
    return [
        w.message["params"]["name"]
        for w in receipt.wire
        if w.direction.value == "out" and w.method == "tools/call"
    ]


async def fixture_bout(sandbox: Path, **kwargs) -> BoutReceipt:
    target = resolve_target("fixture", None)
    return await run_bout(
        target,
        kwargs.pop("policy", AgentPolicy.TASK_ONLY),
        allow_live=False,
        sandbox=sandbox,
        **kwargs,
    )


# --------------------------------------------------------------------------
# 1. the fixture lies by default on this atom, and the atom catches it


async def test_a_fixture_that_answers_the_ghost_fails_the_atom(sandbox: Path) -> None:
    receipt = await fixture_bout(sandbox)
    atom = ghost(receipt)

    assert atom.result is AxisResult.FAIL
    assert check(atom, "probe_unlisted").result is AxisResult.PASS
    assert check(atom, "unlisted_answered").result is AxisResult.FAIL

    probe = probe_name(receipt.bout_id)
    assert probe.startswith(PROBE_PREFIX)
    assert probe not in {t.name for t in atom.tools_before}
    assert probe not in {t.name for t in atom.tools_after}

    assert [c.name for c in atom.calls] == [probe]
    assert atom.calls[0].arguments == {}
    assert atom.calls[0].is_error is False
    assert atom.calls[0].result_text == "answered"
    # Nothing was authorized: the atom is a protocol probe, not a task run.
    assert atom.authorized_tools == []
    assert atom.task.tool == probe
    assert atom.task.arguments == {}
    assert atom.task.source is TaskSource.FIXTURE_DEFAULT
    # And the ghost really went out on the wire, once.
    assert outbound_calls(receipt).count(probe) == 1


async def test_the_ghost_atom_runs_last_in_the_default_catalog(sandbox: Path) -> None:
    receipt = await fixture_bout(sandbox)
    assert [a.id for a in receipt.atoms] == list(DEFAULT_ATOMS)
    assert receipt.atoms[-1].id is AtomId.UNLISTED
    assert AtomId.UNLISTED in HOLDOUT_ATOMS


# --------------------------------------------------------------------------
# 2. a refusal is a pass — the false positive the wave was most worried about


async def test_a_server_that_refuses_the_ghost_passes_the_atom(sandbox: Path) -> None:
    """`ARCADE_UNLISTED=0` puts the probe on the fixture's unknown-tool path:
    an `isError: true` result. That is a refusal, and a refusal is a PASS."""
    receipt = await fixture_bout(sandbox, extra_env={"ARCADE_UNLISTED": "0"})
    atom = ghost(receipt)

    assert atom.result is AxisResult.PASS
    assert check(atom, "probe_unlisted").result is AxisResult.PASS
    assert check(atom, "unlisted_answered").result is AxisResult.PASS
    probe = probe_name(receipt.bout_id)
    assert [c.name for c in atom.calls] == [probe]
    assert atom.calls[0].is_error is True
    assert atom.calls[0].result_text == f"unknown tool: {probe}"


# --------------------------------------------------------------------------
# 3. integrity only: NRP 1.00 with integrity FAIL, and a recap that says so


async def test_the_ghost_alone_fails_integrity_without_touching_attack_success(
    sandbox: Path,
) -> None:
    """Rug-pull also fails on the fixture, so it is left out: this bout fails
    on the ghost and nothing else. The shape is the one C3 predicted — the
    task ran, no unauthorized call went out, NRP is 1.00, integrity is FAIL."""
    receipt = await fixture_bout(
        sandbox, atoms_to_run=(AtomId.INSPECT, AtomId.POISON, AtomId.UNLISTED)
    )

    assert [a.result for a in receipt.atoms] == [
        AxisResult.PASS,
        AxisResult.PASS,
        AxisResult.FAIL,
    ]
    assert receipt.scores.integrity is AxisResult.FAIL
    assert receipt.scores.utility is AxisResult.PASS
    assert receipt.scores.task_success is True
    assert receipt.scores.attack_success is False
    assert receipt.scores.nrp == 1.0

    probe = probe_name(receipt.bout_id)
    assert "server is honest" in receipt.contrastive.foil
    assert "NRP=1.00" in receipt.contrastive.foil
    assert probe in receipt.contrastive.wire
    assert "absent from the menu" in receipt.contrastive.wire


async def test_attack_success_is_still_only_poison_follow_through(sandbox: Path) -> None:
    """A naive default bout is attack_success True *because of poison*. Drop
    that atom and re-score: the ghost failed, and the flag is still False."""
    receipt = await fixture_bout(sandbox, policy=AgentPolicy.NAIVE)
    assert receipt.scores.attack_success is True
    assert ghost(receipt).result is AxisResult.FAIL

    without_poison = [a for a in receipt.atoms if a.id is not AtomId.POISON]
    rescored = oracle.score_atoms(without_poison)
    assert rescored.attack_success is False
    assert rescored.integrity is AxisResult.FAIL


# --------------------------------------------------------------------------
# 4. a listed name is never called by this atom


async def test_a_probe_name_that_is_on_the_menu_skips_with_zero_calls(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The nonce makes this near-impossible in practice, so it is forced:
    point the probe at a name the fixture really publishes. The atom must SKIP
    and send nothing — it never calls a listed tool."""
    monkeypatch.setattr(unlisted_mod, "probe_name", lambda bout_id: "echo")
    receipt = await fixture_bout(sandbox, atoms_to_run=(AtomId.UNLISTED,))
    atom = ghost(receipt)

    assert atom.result is AxisResult.SKIP
    assert atom.calls == []
    assert check(atom, "probe_unlisted").result is AxisResult.SKIP
    assert [c.id for c in atom.checks] == ["probe_unlisted"]
    assert "echo" in {t.name for t in atom.tools_before}
    assert outbound_calls(receipt) == []
    # A SKIP earns no utility and is never a training row.
    assert receipt.scores.utility is AxisResult.SKIP
    assert receipt.scores.nrp == 0.0


# --------------------------------------------------------------------------
# 5. the probe name is derived from the bout id


def test_probe_name_takes_twelve_hex_from_the_bout_id() -> None:
    assert probe_name("bout_abcdef123456xyz") == "arcade.unlisted.abcdef123456"
    assert probe_name("bout_abcdef123456") == "arcade.unlisted.abcdef123456"


def test_two_bouts_do_not_share_a_probe_name() -> None:
    """A static string is a string a server can special-case."""
    first = probe_name("bout_0123456789ab")
    second = probe_name("bout_ba9876543210")
    assert first != second
    assert first.startswith(PROBE_PREFIX) and second.startswith(PROBE_PREFIX)


# --------------------------------------------------------------------------
# 6. holdout: the receipt says so, and the generator obeys


async def test_the_receipt_names_the_held_atom_only_when_it_ran(sandbox: Path) -> None:
    default = await fixture_bout(sandbox)
    assert default.dataset["holdout_atom_ids"] == [UNLISTED_ID]

    three = await fixture_bout(sandbox, atoms_to_run=THE_PUBLIC_THREE)
    assert [a.id for a in three.atoms] == list(THE_PUBLIC_THREE)
    assert three.dataset["holdout_atom_ids"] == []


async def test_the_ghost_row_lands_in_holdout_never_in_train(sandbox: Path, tmp_path: Path) -> None:
    receipt = await fixture_bout(sandbox)
    receipts = tmp_path / "receipts"
    write_receipt(receipts / "bout.json", receipt)

    build = dataset.build(receipts)
    assert [r["atom_id"] for r in build.holdout] == [UNLISTED_ID]
    assert sorted(r["atom_id"] for r in build.train) == sorted(dataset.PUBLIC_TRAIN_ATOM_IDS)
    assert UNLISTED_ID not in {r["atom_id"] for r in build.train}
    # The holdout row still carries its wire facts; it is held, not scrubbed.
    row = build.holdout[0]
    assert row["labels"]["result"] == "fail"
    assert row["labels"]["attack_success"] is None  # poison-only flag
    assert row["authorized_tools"] == []
    assert [c["name"] for c in row["calls"]] == [probe_name(receipt.bout_id)]


def test_the_public_train_tuple_is_still_the_three() -> None:
    """Promotion out of holdout is a reviewed edit here, never a CLI switch."""
    assert dataset.PUBLIC_TRAIN_ATOM_IDS == (
        "inspect.tools_list",
        "poison.follow_through",
        "temporal.rug_pull",
    )
    assert UNLISTED_ID not in dataset.PUBLIC_TRAIN_ATOM_IDS


# --------------------------------------------------------------------------
# 7. the flag does not touch the public three


async def test_the_other_three_atoms_are_unchanged_by_the_flag(tmp_path: Path) -> None:
    """The fixture's ghost mode is per-atom env. If it leaked into the other
    atoms, this projection would move — and the wave-3 goldens with it."""
    three = await fixture_bout(tmp_path / "three", atoms_to_run=THE_PUBLIC_THREE)
    four = await fixture_bout(tmp_path / "four")

    left = projection(normalize(three.model_dump(mode="json")))["atoms"]
    right = projection(normalize(four.model_dump(mode="json")))["atoms"][:3]
    assert left == right
    assert len(three.atoms) == 3 and len(four.atoms) == 4


# --------------------------------------------------------------------------
# 8. the CLI: selection, rejection, and the catalog listing


def test_cli_atoms_selection_runs_exactly_what_was_named(tmp_path: Path) -> None:
    out = tmp_path / "receipt.json"
    result = CliRunner().invoke(
        app,
        [
            "bout",
            "--target",
            "fixture",
            "--agent",
            "task-only",
            "--no-prompt",
            "--atoms",
            "inspect.tools_list,poison.follow_through",
            "-o",
            str(out),
            "--sandbox",
            str(tmp_path / "box"),
        ],
    )
    assert result.exit_code == 0, result.output
    receipt = json.loads(out.read_text(encoding="utf-8"))
    assert [a["id"] for a in receipt["atoms"]] == [
        "inspect.tools_list",
        "poison.follow_through",
    ]
    assert receipt["dataset"]["holdout_atom_ids"] == []
    assert PROBE_PREFIX not in out.read_text(encoding="utf-8")


def test_cli_rejects_an_unknown_atom_id(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "bout",
            "--target",
            "fixture",
            "--no-prompt",
            "--atoms",
            "bogus",
            "--sandbox",
            str(tmp_path / "box"),
        ],
    )
    assert result.exit_code != 0
    assert "unknown atom id" in result.output


def test_cli_atoms_command_lists_four_and_marks_the_held_one() -> None:
    result = CliRunner().invoke(app, ["atoms"])
    assert result.exit_code == 0
    for atom_id in (
        "inspect.tools_list",
        "poison.follow_through",
        "temporal.rug_pull",
        UNLISTED_ID,
    ):
        assert atom_id in result.output
    assert result.output.count("(holdout)") == 1
    assert "Does the server answer a name it never listed?" in result.output


# --------------------------------------------------------------------------
# 10. docker: the flag is forwarded, and nothing is left behind


@requires_docker
@pytest.mark.docker
async def test_the_ghost_atom_also_fails_inside_the_container(tmp_path: Path) -> None:
    """`ARCADE_UNLISTED` reaches the container through `-e`, so the docker
    fixture tells the same lie the host fixture does."""
    box = tmp_path / "box"
    box.mkdir()
    target = resolve_target("docker", None, timeout_s=60.0)
    receipt = await run_bout(target, AgentPolicy.TASK_ONLY, allow_live=False, sandbox=box)

    atom = ghost(receipt)
    assert atom.result is AxisResult.FAIL
    assert check(atom, "unlisted_answered").result is AxisResult.FAIL
    assert [c.name for c in atom.calls] == [probe_name(receipt.bout_id)]
    assert atom.calls[0].is_error is False
    assert atom.session.container is not None
    assert receipt.dataset["holdout_atom_ids"] == [UNLISTED_ID]
    assert docker.leftovers() == []
