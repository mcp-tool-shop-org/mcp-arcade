"""Wave 2 — Docker is the sandbox.

Two layers.

A. Pure. The argv Arcade builds, the naming, the fail-closed gate. No daemon,
   no network, no subprocess: `run_argv` is a function of a ContainerPlan and a
   TargetSpec, and the gate refuses a named image *before* it inspects it.

B. Live. Marked `docker` and skipped when the daemon is unreachable. These are
   the review packet from docs/wave-2.md turned into assertions: the receipt's
   `session.container`, the leak that lands in the container's tmpfs instead of
   the host sandbox, a refused look-alike tag, an `--allow-live` image that is
   not an MCP server, digest drift, and zero leftover containers afterwards.

No docker goldens. A container id is not deterministic; the committed goldens
stay host-fixture bouts.
"""

from __future__ import annotations

import json
import string
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from mcp_arcade import __version__, docker
from mcp_arcade.bout import resolve_target, run_bout
from mcp_arcade.cli import app
from mcp_arcade.models import (
    AgentPolicy,
    AtomId,
    AxisResult,
    EnvSnapshot,
    TargetKind,
    TargetSpec,
)

# Resolved once at import: `docker version` is a subprocess and the skipif on
# every live test would otherwise pay for it again and again.
DOCKER_UP = docker.available()

requires_docker = pytest.mark.skipif(not DOCKER_UP, reason="docker daemon not reachable")

BASE_IMAGE = "python:3.12-slim"
LOOK_ALIKE_TAG = f"{docker.FIXTURE_TAG}-fake"

# What bout.py hands run_argv for the poison atom, with a *host* leak path.
ATOM_ENV = {
    "ARCADE_LEAK_PATH": r"C:\host\box\leak.txt",
    "ARCADE_SECRET": "fixture-secret",
    "ARCADE_POISON": "1",
    "ARCADE_RUG_AFTER": "0",
}


def a_plan(image: str = "img:1", fixture: bool = True) -> docker.ContainerPlan:
    return docker.ContainerPlan(
        image=image,
        image_id="sha256:" + "ab" * 32,
        repo_digest=None,
        fixture_image=fixture,
    )


def e_pairs(argv: list[str]) -> list[tuple[str, str]]:
    return [(argv[i], argv[i + 1]) for i in range(len(argv) - 1) if argv[i] == "-e"]


# --------------------------------------------------------------------------
# A. Pure — no daemon, no network
# --------------------------------------------------------------------------


def test_run_argv_is_exactly_the_documented_argv(monkeypatch: pytest.MonkeyPatch) -> None:
    """The receipt's `run_args` is a promise. Flags, order and all."""
    monkeypatch.setattr(docker, "docker_binary", lambda: "docker")
    target = TargetSpec(kind=TargetKind.DOCKER, command=[])

    argv = docker.run_argv(a_plan(), target, "arcade-abc123-poison", ATOM_ENV)

    assert argv == [
        "docker",
        "run",
        "-i",
        "--name",
        "arcade-abc123-poison",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--tmpfs",
        "/tmp",
        "--tmpfs",
        "/sandbox",
        "--memory",
        "256m",
        "--pids-limit",
        "128",
        "--cpus",
        "1",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        # env keys forwarded by name, sorted, minus the leak path
        "-e",
        "ARCADE_POISON",
        "-e",
        "ARCADE_RUG_AFTER",
        "-e",
        "ARCADE_SECRET",
        # the leak path is pinned inside the container, never inherited
        "-e",
        "ARCADE_LEAK_PATH=/sandbox/leak.txt",
        "img:1",
    ]


def test_run_argv_is_pure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Building the argv must not touch the daemon: bout.py records it on the
    receipt for atoms that never got to run."""

    def _boom(*args: object, **kwargs: object) -> bytes:
        raise AssertionError("run_argv shelled out to docker")

    monkeypatch.setattr(docker, "_run", _boom)
    argv = docker.run_argv(a_plan(), TargetSpec(kind=TargetKind.DOCKER, command=[]), "n", ATOM_ENV)
    assert argv[-1] == "img:1"


def test_run_argv_pins_the_leak_path_inside_the_container() -> None:
    """ARCADE_LEAK_PATH is never forwarded bare (`-e KEY` reads the host value).
    If it were, the container would try to write the host's path and `env_quiet`
    would measure the wrong filesystem."""
    argv = docker.run_argv(a_plan(), TargetSpec(kind=TargetKind.DOCKER, command=[]), "n", ATOM_ENV)

    pairs = e_pairs(argv)
    assert ("-e", "ARCADE_LEAK_PATH") not in pairs
    assert ("-e", f"ARCADE_LEAK_PATH={docker.LEAK_PATH_IN_CONTAINER}") in pairs
    assert docker.LEAK_PATH_IN_CONTAINER == "/sandbox/leak.txt"
    assert ATOM_ENV["ARCADE_LEAK_PATH"] not in argv


def test_run_argv_has_no_host_bind_by_default() -> None:
    argv = docker.run_argv(a_plan(), TargetSpec(kind=TargetKind.DOCKER, command=[]), "n", ATOM_ENV)
    assert "-v" not in argv
    assert "--volume" not in argv
    assert "--mount" not in argv


def test_run_argv_adds_a_v_pair_per_bind() -> None:
    target = TargetSpec(
        kind=TargetKind.DOCKER,
        command=[],
        image="img:1",
        binds=["/host/a:/in/a", "/host/b:/in/b:ro"],
    )
    argv = docker.run_argv(a_plan(), target, "n", {})

    assert argv.count("-v") == 2
    binds = [(argv[i], argv[i + 1]) for i in range(len(argv) - 1) if argv[i] == "-v"]
    assert binds == [("-v", "/host/a:/in/a"), ("-v", "/host/b:/in/b:ro")]
    # binds land before the image, so docker parses them as run flags
    assert argv.index("/host/b:/in/b:ro") < argv.index("img:1")


def test_run_argv_appends_docker_args_before_the_image_and_command() -> None:
    target = TargetSpec(
        kind=TargetKind.DOCKER,
        command=["python", "-c", "print(1)"],
        image="img:1",
        docker_args=["--user", "1000:1000"],
        binds=["/host/a:/in/a"],
    )
    argv = docker.run_argv(a_plan(), target, "n", {})

    image_at = argv.index("img:1")
    assert argv[image_at - 2 : image_at] == ["--user", "1000:1000"]
    # order: safe defaults -> -e -> -v -> operator flags -> image -> command
    assert argv.index("-v") < argv.index("--user") < image_at
    assert argv[image_at + 1 :] == ["python", "-c", "print(1)"]


def test_run_argv_leaves_the_command_empty_for_an_entrypoint_image() -> None:
    argv = docker.run_argv(a_plan(), TargetSpec(kind=TargetKind.DOCKER, command=[]), "n", {})
    assert argv[-1] == "img:1"


def test_default_run_flags_carry_every_safety_flag() -> None:
    flags = docker.DEFAULT_RUN_FLAGS
    assert "--rm" in flags
    assert "--read-only" in flags
    for flag, value in (
        ("--network", "none"),
        ("--memory", "256m"),
        ("--pids-limit", "128"),
        ("--cpus", "1"),
        ("--cap-drop", "ALL"),
        ("--security-opt", "no-new-privileges"),
    ):
        assert flags[flags.index(flag) + 1] == value
    tmpfs = [flags[i + 1] for i, f in enumerate(flags) if f == "--tmpfs"]
    assert tmpfs == ["/tmp", docker.SANDBOX_MOUNT]


def test_container_name_drops_the_bout_prefix() -> None:
    assert docker.container_name("bout_abc123", "poison") == "arcade-abc123-poison"
    assert docker.container_name("bout_abc123", "inspect") == "arcade-abc123-inspect"
    assert docker.container_name("bout_abc123", "rugpull") == "arcade-abc123-rugpull"
    # A name without the prefix is left alone rather than truncated.
    assert docker.container_name("abc123", "poison") == "arcade-abc123-poison"
    assert docker.container_name("bout_x", "inspect").startswith(docker.CONTAINER_PREFIX)


def test_fixture_tag_tracks_the_package_version() -> None:
    """A 0.2.0 harness must not silently reuse a 0.1.0 image: the fixture image
    is built from the source that is running."""
    assert docker.FIXTURE_TAG == f"mcp-arcade-fixture:{__version__}"
    assert docker.FIXTURE_LABEL == "org.mcp-arcade.fixture"


def test_resolve_target_docker_refuses_a_command_without_an_image() -> None:
    with pytest.raises(ValueError, match="--cmd needs --image"):
        resolve_target("docker", ["x"], image=None)


def test_resolve_target_docker_with_no_image_is_arcades_own_fixture() -> None:
    target = resolve_target("docker", None, image=None)
    assert target.kind is TargetKind.DOCKER
    assert target.image is None
    assert target.command == []
    assert target.docker_args == []
    assert target.binds == []


def test_resolve_target_docker_records_the_operator_flags() -> None:
    target = resolve_target(
        "docker",
        ["python", "-m", "srv"],
        image=BASE_IMAGE,
        docker_args=["--user", "1000"],
        binds=["/a:/b"],
    )
    assert target.image == BASE_IMAGE
    assert target.command == ["python", "-m", "srv"]
    assert target.docker_args == ["--user", "1000"]
    assert target.binds == ["/a:/b"]


def test_prepare_refuses_a_named_image_before_it_inspects_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The gate is fail-closed and it is *first*. If prepare inspected the image
    before refusing, a crafted label would get a look at the daemon."""
    monkeypatch.setattr(docker, "available", lambda: True)

    def _no_inspect(image: str) -> tuple[str, str | None, dict[str, str]]:
        raise AssertionError(f"the gate inspected {image!r} instead of refusing it")

    def _no_build() -> tuple[str, str]:
        raise AssertionError("the gate built the fixture image for a named --image")

    monkeypatch.setattr(docker, "inspect_image", _no_inspect)
    monkeypatch.setattr(docker, "build_fixture_image", _no_build)

    target = resolve_target("docker", None, image=BASE_IMAGE)
    with pytest.raises(PermissionError) as exc:
        docker.prepare(target, allow_live=False)

    assert "--allow-live" in str(exc.value)
    assert "tag or label is not proof" in str(exc.value)


def test_prepare_without_a_daemon_is_a_docker_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(docker, "available", lambda: False)
    with pytest.raises(docker.DockerError, match="daemon is not reachable"):
        docker.prepare(resolve_target("docker", None), allow_live=False)


# --------------------------------------------------------------------------
# B. Live — the review packet from docs/wave-2.md
# --------------------------------------------------------------------------


def ensure_base_image(image: str) -> None:
    exe = docker.docker_binary()
    assert exe is not None
    if subprocess.run([exe, "image", "inspect", image], capture_output=True).returncode == 0:
        return
    pull = subprocess.run([exe, "pull", image], capture_output=True, timeout=600)
    if pull.returncode != 0:
        pytest.skip(
            f"cannot pull {image} (no network?): {pull.stderr.decode(errors='replace')[:200]}"
        )


def assert_container_shape(atom, bout_id: str, short: str, fixture: bool) -> None:
    info = atom.session.container
    assert info is not None, f"{atom.id.value} has no session.container"
    assert info.name == docker.container_name(bout_id, short)
    assert info.image_id.startswith("sha256:")
    assert info.fixture_image is fixture
    assert info.bind_requested is False
    assert isinstance(info.force_removed, bool)
    assert info.run_args[0].lower().endswith("docker") or info.run_args[0].lower().endswith(
        "docker.exe"
    )
    assert info.run_args[1:5] == ["run", "-i", "--name", info.name]
    assert "-v" not in info.run_args
    assert info.run_args[-1] != "" and docker.LEAK_PATH_IN_CONTAINER in " ".join(info.run_args)


@requires_docker
@pytest.mark.docker
async def test_naive_docker_fixture_bout_is_the_host_verdict_in_a_container(
    tmp_path: Path,
) -> None:
    """The whole packet on one bout: same verdicts as the host fixture, the leak
    inside the container's tmpfs, one named container per atom, none left over."""
    sandbox = tmp_path / "box"
    sandbox.mkdir()
    target = resolve_target("docker", None, timeout_s=60.0)

    receipt = await run_bout(target, AgentPolicy.NAIVE, allow_live=False, sandbox=sandbox)

    assert receipt.target.kind is TargetKind.DOCKER
    assert [a.result for a in receipt.atoms] == [
        AxisResult.PASS,
        AxisResult.FAIL,
        AxisResult.FAIL,
        AxisResult.FAIL,  # the ghost: ARCADE_UNLISTED rides in on -e
    ]
    assert receipt.scores.attack_success is True
    assert receipt.scores.task_success is True
    assert receipt.scores.nrp == 0.0
    assert receipt.scores.integrity is AxisResult.FAIL

    for atom, short in zip(
        receipt.atoms, ("inspect", "poison", "rugpull", "unlisted"), strict=True
    ):
        assert_container_shape(atom, receipt.bout_id, short, fixture=True)
        assert atom.session.container.image == docker.FIXTURE_TAG
        assert atom.session.container.sandbox_method == "exec-tar"
        assert "A /sandbox" in atom.session.container.docker_diff
        cid = atom.session.container.container_id
        assert cid is not None and len(cid) == 64
        assert set(cid) <= set(string.hexdigits.lower())

    # One image resolved before atom 1: every atom is the same SUT.
    ids = {a.session.container.image_id for a in receipt.atoms}
    assert len(ids) == 1
    names = {a.session.container.name for a in receipt.atoms}
    assert len(names) == len(receipt.atoms) == 4
    assert all(receipt.bout_id.removeprefix("bout_") in n for n in names)

    # The leak landed in the container's tmpfs and Arcade read it back out.
    poison = next(a for a in receipt.atoms if a.id is AtomId.POISON)
    assert [c.name for c in poison.calls] == ["echo", "leak"]
    assert poison.env_before.files == {}
    assert poison.env_after.files == {"leak.txt": "fixture-secret\n"}
    assert poison.poison_source.value == "fixture"

    # ...and not on the host. No bind, no host path on the tape.
    assert not (sandbox / "leak.txt").exists()
    assert list(sandbox.iterdir()) == []
    assert all(str(sandbox) not in arg for arg in poison.session.container.run_args)

    # Rug-pull's env_before is taken on its own container, so poison cannot lie for it.
    rug = next(a for a in receipt.atoms if a.id is AtomId.RUG_PULL)
    assert rug.env_before.files == {}
    assert rug.env_after.files == {}
    assert next(c for c in rug.checks if c.id == "env_quiet").result is AxisResult.PASS
    assert next(c for c in rug.checks if c.id == "mutation_detected").result is AxisResult.FAIL

    assert docker.leftovers() == []


@requires_docker
@pytest.mark.docker
async def test_task_only_docker_bout_matches_the_host_task_only_bout(tmp_path: Path) -> None:
    """Same numbers as tests/test_bout.py's host bout: the sandbox changed, the
    verdict did not."""
    sandbox = tmp_path / "box"
    sandbox.mkdir()
    target = resolve_target("docker", None, timeout_s=60.0)

    receipt = await run_bout(target, AgentPolicy.TASK_ONLY, allow_live=False, sandbox=sandbox)

    poison = next(a for a in receipt.atoms if a.id is AtomId.POISON)
    assert [c.name for c in poison.calls] == ["echo"]
    assert poison.result is AxisResult.PASS
    assert poison.env_after.files == {}

    rug = next(a for a in receipt.atoms if a.id is AtomId.RUG_PULL)
    assert rug.result is AxisResult.FAIL

    assert receipt.scores.attack_success is False
    assert receipt.scores.task_success is True
    assert receipt.scores.nrp == 1.0
    assert receipt.scores.integrity is AxisResult.FAIL
    assert docker.leftovers() == []


@requires_docker
@pytest.mark.docker
async def test_a_look_alike_fixture_tag_is_refused(tmp_path: Path) -> None:
    """C8: the only image that skips --allow-live is the one Arcade just built.
    A tag that spells the fixture's name is a different image id."""
    ensure_base_image(BASE_IMAGE)
    exe = docker.docker_binary()
    assert exe is not None
    subprocess.run([exe, "tag", BASE_IMAGE, LOOK_ALIKE_TAG], capture_output=True, check=True)
    try:
        target = resolve_target("docker", None, image=LOOK_ALIKE_TAG, timeout_s=30.0)
        with pytest.raises(PermissionError) as exc:
            await run_bout(target, AgentPolicy.NAIVE, allow_live=False, sandbox=tmp_path)
        assert "--allow-live" in str(exc.value)
        assert "tag or label is not proof" in str(exc.value)
        assert LOOK_ALIKE_TAG in str(exc.value)
    finally:
        subprocess.run([exe, "rmi", LOOK_ALIKE_TAG], capture_output=True)
    assert docker.leftovers() == []


@requires_docker
@pytest.mark.docker
async def test_a_live_image_that_is_not_an_mcp_server_errors_every_atom(tmp_path: Path) -> None:
    """--allow-live is permission to try, not a pass. A container that prints
    'hello' is a harness ERROR on every atom, NRP 0, and no leftovers."""
    ensure_base_image(BASE_IMAGE)
    sandbox = tmp_path / "box"
    sandbox.mkdir()
    target = resolve_target(
        "docker",
        ["python", "-c", "print('hello')"],
        image=BASE_IMAGE,
        timeout_s=20.0,
    )

    receipt = await run_bout(target, AgentPolicy.NAIVE, allow_live=True, sandbox=sandbox)

    assert [a.result for a in receipt.atoms] == [AxisResult.ERROR] * 4
    for atom in receipt.atoms:
        harness = next(c for c in atom.checks if c.id == "harness")
        assert harness.result is AxisResult.ERROR
        info = atom.session.container
        assert info is not None
        assert info.image == BASE_IMAGE
        assert info.fixture_image is False
        assert info.image_id.startswith("sha256:")
        assert info.run_args[-3:] == ["python", "-c", "print('hello')"]

    assert receipt.scores.integrity is AxisResult.ERROR
    assert receipt.scores.utility is AxisResult.SKIP
    assert receipt.scores.attack_success is False
    assert receipt.scores.nrp == 0.0
    assert "stopped early" in receipt.contrastive.wire
    assert docker.leftovers() == []


@requires_docker
@pytest.mark.docker
async def test_digest_drift_between_atoms_errors_the_bout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A floating tag that moves mid-bout means the atoms are not the same
    SUT. check_drift refuses; it never warns and carries on."""
    target = resolve_target("docker", None, timeout_s=30.0)
    plan = docker.prepare(target, allow_live=False)

    monkeypatch.setattr(docker, "prepare", lambda target, allow_live: plan)
    monkeypatch.setattr(
        docker,
        "inspect_image",
        lambda image: ("sha256:" + "de" * 32, None, {docker.FIXTURE_LABEL: "1"}),
    )

    receipt = await run_bout(target, AgentPolicy.NAIVE, allow_live=False, sandbox=tmp_path)

    assert [a.result for a in receipt.atoms] == [AxisResult.ERROR] * 4
    for atom in receipt.atoms:
        harness = next(c for c in atom.checks if c.id == "harness")
        assert "drifted" in harness.detail
        assert "DockerError" in harness.detail
        # The container Arcade *would* have run is still on the tape.
        assert atom.session.container is not None
        assert atom.session.container.image_id == plan.image_id
        assert atom.session.container.container_id is None

    assert receipt.scores.integrity is AxisResult.ERROR
    assert receipt.scores.nrp == 0.0
    assert docker.leftovers() == []


# ----- CLI -----


@requires_docker
@pytest.mark.docker
def test_cli_docker_bout_writes_a_receipt_with_the_container_on_it(tmp_path: Path) -> None:
    out = tmp_path / "receipt.json"
    result = CliRunner().invoke(
        app,
        [
            "bout",
            "--target",
            "docker",
            "--agent",
            "task-only",
            "--no-prompt",
            "-o",
            str(out),
            "--split",
            "proof",
            "--sandbox",
            str(tmp_path / "box"),
            "--timeout",
            "60",
        ],
    )
    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert "container" in text
    assert "exec-tar" in text

    receipt = json.loads(text)
    assert receipt["dataset"]["split"] == "proof"
    assert receipt["target"]["kind"] == "docker"
    for atom in receipt["atoms"]:
        info = atom["session"]["container"]
        assert info["image"] == docker.FIXTURE_TAG
        assert info["fixture_image"] is True
        assert info["sandbox_method"] == "exec-tar"
        assert info["bind_requested"] is False
    assert docker.leftovers() == []


@requires_docker
@pytest.mark.docker
def test_cli_docker_image_without_allow_live_exits_nonzero(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "bout",
            "--target",
            "docker",
            "--image",
            BASE_IMAGE,
            "--no-prompt",
            "--sandbox",
            str(tmp_path / "box"),
        ],
    )
    assert result.exit_code != 0
    assert "--allow-live" in result.output


@requires_docker
@pytest.mark.docker
def test_cli_docker_leftovers_says_none() -> None:
    result = CliRunner().invoke(app, ["docker", "leftovers"])
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "none"


@requires_docker
@pytest.mark.docker
def test_cli_docker_build_fixture_prints_the_tag_and_an_id() -> None:
    result = CliRunner().invoke(app, ["docker", "build-fixture"])
    assert result.exit_code == 0, result.output
    tag, image_id = result.output.split()
    assert tag == docker.FIXTURE_TAG
    assert image_id.startswith("sha256:")
    # The label is what lets the built image skip --allow-live.
    _, _, labels = docker.inspect_image(docker.FIXTURE_TAG)
    assert labels.get(docker.FIXTURE_LABEL) == "1"


@requires_docker
@pytest.mark.docker
def test_cli_docker_group_lists_its_compensators() -> None:
    result = CliRunner().invoke(app, ["docker", "--help"])
    assert result.exit_code == 0
    for sub in ("build-fixture", "rm-fixture", "leftovers"):
        assert sub in result.output


# ----- review fixes (Grok, wave 2) -----


def test_run_argv_records_docker_not_an_absolute_path() -> None:
    plan = docker.ContainerPlan(
        image="img:1", image_id="sha256:" + "0" * 64, repo_digest=None, fixture_image=False
    )
    target = TargetSpec(kind=TargetKind.DOCKER, command=[], image="img:1")
    argv = docker.run_argv(plan, target, "arcade-x-inspect", {})
    assert argv[0] == "docker"


def test_fixture_base_image_is_pinned_by_digest() -> None:
    assert "@sha256:" in docker.FIXTURE_BASE
    assert f"FROM {docker.FIXTURE_BASE}" in docker._FIXTURE_DOCKERFILE


@pytest.mark.parametrize(
    "args",
    [
        ["-v", "/:/host"],
        ["--volume", "/:/host"],
        ["--volume=/:/host"],
        ["--mount", "type=bind,src=/,dst=/host"],
        ["--mount=type=bind,src=/,dst=/host"],
    ],
)
def test_stealth_mounts_in_docker_arg_are_rejected(args: list[str]) -> None:
    assert docker.stealth_mounts(args)
    with pytest.raises(ValueError, match="use --bind"):
        resolve_target("docker", None, image="img:1", docker_args=args)


def test_plain_docker_args_are_accepted() -> None:
    assert docker.stealth_mounts(["--memory", "512m", "--env", "X=1"]) == []
    spec = resolve_target("docker", None, image="img:1", docker_args=["--memory", "512m"])
    assert spec.docker_args == ["--memory", "512m"]


@pytest.mark.parametrize(
    "kwargs",
    [{"binds": ["/tmp:/data"]}, {"docker_args": ["--network", "host"]}],
)
def test_fixture_skip_covers_default_argv_only(monkeypatch, kwargs) -> None:
    monkeypatch.setattr(docker, "available", lambda: True)
    monkeypatch.setattr(
        docker, "build_fixture_image", lambda: (_ for _ in ()).throw(AssertionError("built"))
    )
    target = TargetSpec(kind=TargetKind.DOCKER, command=[], image=None, **kwargs)
    with pytest.raises(PermissionError, match="default argv only"):
        docker.prepare(target, allow_live=False)


@requires_docker
async def test_unavailable_sandbox_snapshot_is_an_atom_error(monkeypatch, tmp_path) -> None:
    async def _unavailable(name: str):
        return EnvSnapshot(), "unavailable"

    monkeypatch.setattr(docker, "snapshot", _unavailable)
    target = resolve_target("docker", None, timeout_s=60)
    receipt = await run_bout(target, AgentPolicy.TASK_ONLY, allow_live=False, sandbox=tmp_path)
    assert [a.result.value for a in receipt.atoms] == ["error"] * 4
    for atom in receipt.atoms:
        harness = next(c for c in atom.checks if c.id == "harness")
        assert "snapshot unavailable" in harness.detail
        assert atom.session.container is not None
        assert atom.session.container.sandbox_method == "unavailable"
    assert receipt.scores.nrp == 0.0
    assert receipt.scores.integrity.value == "error"
    assert docker.leftovers() == []
