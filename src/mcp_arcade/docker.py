"""Docker is the sandbox (wave 2).

Everything Docker lives here: the argv Arcade builds, digest resolution, the
per-atom sandbox snapshot, `docker diff`, the force-remove compensator, and
the local fixture image build. `bout.py` asks for these by target kind; the
oracle does not know Docker exists.

Safe defaults (all on, operators loosen only with explicit, recorded flags):
  -i --rm --network none --read-only --tmpfs /tmp --tmpfs /sandbox
  --memory 256m --pids-limit 128 --cpus 1 --cap-drop ALL
  --security-opt no-new-privileges --name arcade-<bout_id>-<atom>

No host bind mounts unless the operator passes --bind, and then the receipt
says so.
"""

from __future__ import annotations

import asyncio
import io
import json
import shutil
import subprocess
import tarfile
from dataclasses import dataclass, field
from pathlib import Path

from mcp_arcade import __version__
from mcp_arcade.models import EnvSnapshot, TargetSpec

SANDBOX_MOUNT = "/sandbox"
LEAK_PATH_IN_CONTAINER = f"{SANDBOX_MOUNT}/leak.txt"
FIXTURE_LABEL = "org.mcp-arcade.fixture"
FIXTURE_TAG = f"mcp-arcade-fixture:{__version__}"
CONTAINER_PREFIX = "arcade-"

DEFAULT_RUN_FLAGS: tuple[str, ...] = (
    "--rm",
    "--network",
    "none",
    "--read-only",
    "--tmpfs",
    "/tmp",
    "--tmpfs",
    SANDBOX_MOUNT,
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
)

_FIXTURE_DOCKERFILE = """\
FROM python:3.12-slim
LABEL org.mcp-arcade.fixture=1
COPY . /app/mcp_arcade
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
ENTRYPOINT ["python", "-m", "mcp_arcade.fixture"]
"""


class DockerError(RuntimeError):
    pass


@dataclass
class ContainerPlan:
    """Resolved once before atom 1 and reused for all atoms."""

    image: str
    image_id: str
    repo_digest: str | None
    fixture_image: bool
    labels: dict[str, str] = field(default_factory=dict)


def docker_binary() -> str | None:
    return shutil.which("docker")


def available() -> bool:
    exe = docker_binary()
    if exe is None:
        return False
    try:
        out = subprocess.run(
            [exe, "version", "--format", "{{.Server.Version}}"],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return out.returncode == 0 and bool(out.stdout.strip())


def _run(args: list[str], timeout: float = 60, input_bytes: bytes | None = None) -> bytes:
    exe = docker_binary()
    if exe is None:
        raise DockerError("docker is not on PATH")
    try:
        out = subprocess.run(
            [exe, *args],
            capture_output=True,
            timeout=timeout,
            input=input_bytes,
        )
    except subprocess.TimeoutExpired as exc:
        raise DockerError(f"docker {args[0]} timed out after {timeout:g}s") from exc
    except OSError as exc:
        raise DockerError(f"docker {args[0]} failed to start: {exc}") from exc
    if out.returncode != 0:
        err = out.stderr.decode("utf-8", errors="replace").strip()
        raise DockerError(f"docker {' '.join(args[:2])} exited {out.returncode}: {err[:400]}")
    return out.stdout


def inspect_image(image: str) -> tuple[str, str | None, dict[str, str]]:
    """Image id (content-addressed), first repo digest if any, labels.

    The whole Config is taken as JSON: dereferencing `.Config.Labels` in the Go
    template errors on images that carry no labels at all."""
    fmt = "{{.Id}}\n{{if .RepoDigests}}{{index .RepoDigests 0}}{{end}}\n{{json .Config}}"
    try:
        raw = _run(["image", "inspect", "--format", fmt, image], timeout=30)
    except DockerError as exc:
        raise DockerError(f"image {image!r} is not available locally: {exc}") from exc
    lines = raw.decode("utf-8", errors="replace").split("\n", 2)
    image_id = lines[0].strip()
    repo_digest = lines[1].strip() or None if len(lines) > 1 else None
    labels: dict[str, str] = {}
    if len(lines) > 2 and lines[2].strip() and lines[2].strip() != "null":
        try:
            config = json.loads(lines[2])
        except json.JSONDecodeError:
            config = {}
        raw_labels = config.get("Labels") if isinstance(config, dict) else None
        if isinstance(raw_labels, dict):
            labels = {str(k): str(v) for k, v in raw_labels.items()}
    if not image_id.startswith("sha256:"):
        raise DockerError(f"could not resolve an image id for {image!r}: {image_id!r}")
    return image_id, repo_digest, labels


def _context_tar() -> bytes:
    """Build context as a tar stream: the Dockerfile plus the package source,
    without __pycache__ or *.pyc, so the image id is stable whenever the source
    is (PIN_PER_STEP) and the layer cache is not busted by bytecode churn."""
    root = Path(__file__).resolve().parent
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        data = _FIXTURE_DOCKERFILE.encode("utf-8")
        info = tarfile.TarInfo("Dockerfile")
        info.size = len(data)
        info.mtime = 0
        tar.addfile(info, io.BytesIO(data))
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            if "__pycache__" in rel or rel.endswith((".pyc", ".pyo")):
                continue
            info = tar.gettarinfo(str(path), arcname=rel)
            info.mtime = 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            with open(path, "rb") as fh:
                tar.addfile(info, fh)
    return buf.getvalue()


def build_fixture_image() -> tuple[str, str]:
    """Build Arcade's own fixture image from the installed package. Returns
    (tag, image_id). The context is a tar stream on stdin (Dockerfile + source,
    no bytecode), so the image contains exactly the source running this harness."""
    raw = _run(
        # No provenance/SBOM attestations: they carry timestamps and would give a
        # fresh image id on every build even when every layer is cached.
        ["build", "-q", "--provenance=false", "--sbom=false", "-t", FIXTURE_TAG, "-"],
        timeout=600,
        input_bytes=_context_tar(),
    )
    built = raw.decode("utf-8", errors="replace").strip().splitlines()
    image_id = built[-1].strip() if built else ""
    if not image_id.startswith("sha256:"):
        # Some daemons print the short id; normalise through inspect.
        image_id, _, _ = inspect_image(FIXTURE_TAG)
    return FIXTURE_TAG, image_id


def remove_fixture_image() -> bool:
    try:
        _run(["rmi", FIXTURE_TAG], timeout=60)
    except DockerError:
        return False
    return True


def prepare(target: TargetSpec, allow_live: bool) -> ContainerPlan:
    """Resolve the image once, before atom 1, and apply the fail-closed gate.

    The only image that may skip --allow-live is the one Arcade builds itself
    right now (no --image given). An operator-named image always needs
    --allow-live, whatever its tag or label says (C8).
    """
    if not available():
        raise DockerError("docker daemon is not reachable (docker version failed)")
    if target.image is None:
        tag, built_id = build_fixture_image()
        image_id, repo_digest, labels = inspect_image(tag)
        if image_id != built_id or labels.get(FIXTURE_LABEL) != "1":
            raise DockerError(
                f"fixture image {tag} does not match what Arcade just built "
                f"(built {built_id[:19]}, found {image_id[:19]}, label={labels.get(FIXTURE_LABEL)!r})"
            )
        return ContainerPlan(
            image=tag, image_id=image_id, repo_digest=repo_digest, fixture_image=True, labels=labels
        )
    if not allow_live:
        raise PermissionError(
            f"refusing to run image {target.image!r} without --allow-live (C8 fail-closed). "
            "Only the fixture image Arcade builds itself may skip it; a tag or label is not proof."
        )
    image_id, repo_digest, labels = inspect_image(target.image)
    return ContainerPlan(
        image=target.image,
        image_id=image_id,
        repo_digest=repo_digest,
        fixture_image=False,
        labels=labels,
    )


def check_drift(plan: ContainerPlan) -> None:
    """Re-inspect immediately before `docker run`. A floating tag that moved
    between atoms means the three atoms are not the same SUT."""
    image_id, _, _ = inspect_image(plan.image)
    if image_id != plan.image_id:
        raise DockerError(
            f"image {plan.image!r} drifted: resolved {plan.image_id[:19]} before atom 1, "
            f"now {image_id[:19]}"
        )


def container_name(bout_id: str, atom_short: str) -> str:
    return f"{CONTAINER_PREFIX}{bout_id.removeprefix('bout_')}-{atom_short}"


def run_argv(
    plan: ContainerPlan,
    target: TargetSpec,
    name: str,
    env: dict[str, str],
) -> list[str]:
    """The exact argv Arcade runs. Env keys are forwarded by name (docker reads
    the value from its own environment, which the client sets); the leak path
    is pinned inside the container regardless of the host value."""
    exe = docker_binary() or "docker"
    argv: list[str] = [exe, "run", "-i", "--name", name, *DEFAULT_RUN_FLAGS]
    for key in sorted(env):
        if key == "ARCADE_LEAK_PATH":
            continue
        argv += ["-e", key]
    argv += ["-e", f"ARCADE_LEAK_PATH={LEAK_PATH_IN_CONTAINER}"]
    for bind in target.binds:
        argv += ["-v", bind]
    argv += list(target.docker_args)
    argv.append(plan.image)
    argv += list(target.command)
    return argv


async def snapshot(name: str) -> tuple[EnvSnapshot, str]:
    """Contents of /sandbox inside a running container, via `docker exec tar`.
    Returns (snapshot, method). Method is 'unavailable' if the container is
    gone or has no tar; the caller records that rather than guessing."""

    def _snap() -> tuple[EnvSnapshot, str]:
        try:
            raw = _run(["exec", name, "tar", "-C", SANDBOX_MOUNT, "-cf", "-", "."], timeout=30)
        except DockerError:
            return EnvSnapshot(), "unavailable"
        files: dict[str, str] = {}
        try:
            with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as tar:
                for member in tar.getmembers():
                    if not member.isfile():
                        continue
                    fh = tar.extractfile(member)
                    if fh is None:
                        continue
                    rel = member.name.removeprefix("./")
                    files[rel] = fh.read().decode("utf-8", errors="replace")
        except tarfile.TarError:
            return EnvSnapshot(), "unavailable"
        return EnvSnapshot(files=dict(sorted(files.items()))), "exec-tar"

    return await asyncio.to_thread(_snap)


async def diff(name: str) -> list[str]:
    """`docker diff` as a path list ("A /path", "C /path", "D /path"). Names,
    not bytes. tmpfs mounts do not show here; /sandbox contents come from
    snapshot()."""

    def _diff() -> list[str]:
        try:
            raw = _run(["diff", name], timeout=30)
        except DockerError:
            return []
        return [
            ln.strip() for ln in raw.decode("utf-8", errors="replace").splitlines() if ln.strip()
        ]

    return await asyncio.to_thread(_diff)


async def container_id(name: str) -> str | None:
    def _id() -> str | None:
        try:
            raw = _run(["inspect", "--format", "{{.Id}}", name], timeout=30)
        except DockerError:
            return None
        value = raw.decode("utf-8", errors="replace").strip()
        return value or None

    return await asyncio.to_thread(_id)


async def remove(name: str) -> bool:
    """Compensator: force-remove the named container. True if something was
    there to remove (i.e. --rm had not reaped it yet)."""

    def _rm() -> bool:
        try:
            _run(["rm", "-f", name], timeout=60)
        except DockerError:
            return False
        return True

    return await asyncio.to_thread(_rm)


def leftovers() -> list[str]:
    """Names of arcade-* containers still present. Used by tests and the packet."""
    try:
        raw = _run(
            ["ps", "-a", "--filter", f"name={CONTAINER_PREFIX}", "--format", "{{.Names}}"],
            timeout=30,
        )
    except DockerError:
        return []
    return [ln.strip() for ln in raw.decode("utf-8", errors="replace").splitlines() if ln.strip()]
