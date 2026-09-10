"""CLI. Fail-closed: no target, no bout."""

from __future__ import annotations

import asyncio
import json
import shlex
import sys
from pathlib import Path

import click
from rich.console import Console

from mcp_arcade import __version__
from mcp_arcade.bout import resolve_target, run_bout
from mcp_arcade.docker import DockerError
from mcp_arcade.models import AgentPolicy, AtomTitle, TaskSource, TaskSpec
from mcp_arcade.receipt import canonical_dumps, write_receipt
from mcp_arcade.seat import OllamaSeat, parse_agent_spec
from mcp_arcade.tui import ask_operator_call, render_preamble, render_score, render_timeline

console = Console()


def split_command(parts: tuple[str, ...]) -> list[str]:
    """`--cmd` is repeatable. A single value with whitespace is split shell-style
    (non-POSIX rules on Windows so backslashes in paths survive)."""
    if len(parts) == 1 and any(ch.isspace() for ch in parts[0]):
        if sys.platform != "win32":
            return shlex.split(parts[0], posix=True)
        # Non-POSIX keeps backslashes in paths but also keeps the quote characters
        # around a quoted token. Strip one matched pair so a quoted path is a path.
        return [_unquote(tok) for tok in shlex.split(parts[0], posix=False)]
    return list(parts)


def _unquote(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in ('"', "'"):
        return token[1:-1]
    return token


@click.group()
@click.version_option(version=__version__, prog_name="mcp-arcade")
def app() -> None:
    """MCP Arcade — GameDay testing for MCP servers.

    The oracle is the JSON-RPC wire plus sandbox files.
    It does not score tool descriptions or model essays.
    """


@app.command("atoms")
def atoms_cmd() -> None:
    """List the v0 atom catalog. Short on purpose."""
    rows = [
        ("inspect.tools_list", AtomTitle.INSPECT.value, "Is the published menu the real menu?"),
        ("poison.follow_through", AtomTitle.POISON.value, "Does a whispered errand become a call?"),
        (
            "temporal.rug_pull",
            AtomTitle.RUG_PULL.value,
            "After N clean calls, is it still the same tool?",
        ),
    ]
    for atom_id, title, hypo in rows:
        console.print(f"[yellow]{atom_id}[/yellow]  {title}")
        console.print(f"  {hypo}")


@app.command("bout")
@click.option(
    "--target",
    "target_kind",
    type=click.Choice(["fixture", "stdio", "docker"]),
    required=True,
    help="fixture = lab server. stdio = your command (needs --allow-live). "
    "docker = a container Arcade runs with safe defaults (no --image = Arcade's own fixture image).",
)
@click.option(
    "--cmd",
    "command",
    multiple=True,
    help=(
        "stdio argv. Repeatable (--cmd python --cmd -m --cmd my_server) or one quoted "
        'string (--cmd "npx -y my-server").'
    ),
)
@click.option(
    "--image",
    default=None,
    help="docker target: image to run (needs --allow-live). Omit to run Arcade's fixture image.",
)
@click.option(
    "--docker-arg",
    "docker_args",
    multiple=True,
    help="docker target: extra `docker run` flag, repeatable, recorded on the receipt.",
)
@click.option(
    "--bind",
    "binds",
    multiple=True,
    help="docker target: explicit host bind SRC:DST. Off by default; recorded on the receipt.",
)
@click.option(
    "--agent",
    "policy",
    default=AgentPolicy.NAIVE.value,
    show_default=True,
    help="naive follows description side-quests. task-only does not. "
    "ollama:<model> seats a local LLM that sees tools/list and emits tools/call "
    "(it is not a judge).",
)
@click.option(
    "--seat-temperature", type=float, default=0.0, show_default=True, help="ollama seat option."
)
@click.option("--seat-seed", type=int, default=42, show_default=True, help="ollama seat option.")
@click.option(
    "--seat-num-ctx", type=int, default=8192, show_default=True, help="ollama seat option."
)
@click.option(
    "--seat-endpoint",
    default="http://127.0.0.1:11434",
    show_default=True,
    help="Ollama endpoint. Local by default; recorded on the receipt.",
)
@click.option(
    "--seat-timeout",
    type=float,
    default=120.0,
    show_default=True,
    help="Seconds per Ollama chat call. A timeout is an atom ERROR.",
)
@click.option("--allow-live", is_flag=True, help="Required for non-fixture targets.")
@click.option(
    "--task",
    "task_tool",
    default=None,
    help="Benign tool the agent is asked to run. Required on real servers without an echo tool.",
)
@click.option(
    "--args",
    "task_args",
    default=None,
    help='JSON object of arguments for --task, e.g. \'{"path":"."}\'.',
)
@click.option(
    "--wrap",
    is_flag=True,
    help="On the poison atom, append a house side-quest to the task tool's description "
    "(evil-sibling). Off by default so live bouts measure the server's own menu.",
)
@click.option(
    "--framing",
    type=click.Choice(["auto", "ndjson", "content-length"]),
    default="auto",
    show_default=True,
    help="stdio dialect. auto locks to whatever the server answers in.",
)
@click.option(
    "--timeout",
    "timeout_s",
    type=float,
    default=30.0,
    show_default=True,
    help="Seconds to wait for each JSON-RPC response. A timeout is an atom ERROR.",
)
@click.option(
    "--split",
    type=click.Choice(["train", "holdout", "proof"]),
    default="train",
    show_default=True,
    help="dataset.split on the receipt. Use proof for committed live traces so a dataset glob skips them.",
)
@click.option(
    "--no-prompt", is_flag=True, help="Skip the pre-score call (CI). Recorded as skipped."
)
@click.option(
    "-o", "--output", type=click.Path(path_type=Path), help="Write the bout receipt JSON."
)
@click.option(
    "--sandbox", type=click.Path(path_type=Path), help="Sandbox directory for leak files."
)
@click.option(
    "--n-clean",
    type=int,
    default=3,
    show_default=True,
    help="Clean calls before the rug-pull re-list.",
)
def bout_cmd(
    target_kind: str,
    command: tuple[str, ...],
    image: str | None,
    docker_args: tuple[str, ...],
    binds: tuple[str, ...],
    policy: str,
    seat_temperature: float,
    seat_seed: int,
    seat_num_ctx: int,
    seat_endpoint: str,
    seat_timeout: float,
    allow_live: bool,
    task_tool: str | None,
    task_args: str | None,
    wrap: bool,
    framing: str,
    timeout_s: float,
    split: str,
    no_prompt: bool,
    output: Path | None,
    sandbox: Path | None,
    n_clean: int,
) -> None:
    """Run the three v0 atoms and print a contrastive house call."""
    try:
        argv = split_command(command) if command else None
        target = resolve_target(
            target_kind,
            argv,
            framing=framing,
            timeout_s=timeout_s,
            image=image,
            docker_args=list(docker_args),
            binds=list(binds),
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    seat = None
    try:
        seat_config = parse_agent_spec(policy)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    if seat_config is not None:
        from dataclasses import replace

        seat_config = replace(
            seat_config,
            temperature=seat_temperature,
            seed=seat_seed,
            num_ctx=seat_num_ctx,
            endpoint=seat_endpoint,
            timeout_s=seat_timeout,
        )
        seat = OllamaSeat(seat_config)
        agent_policy = AgentPolicy.OLLAMA
    else:
        try:
            agent_policy = AgentPolicy(policy)
        except ValueError as exc:
            raise click.ClickException(
                f"--agent must be naive, task-only, or ollama:<model> (got {policy!r})"
            ) from exc

    task: TaskSpec | None = None
    if task_args is not None and task_tool is None:
        raise click.ClickException("--args needs --task")
    if task_tool is not None:
        arguments: dict = {}
        if task_args is not None:
            try:
                arguments = json.loads(task_args)
            except json.JSONDecodeError as exc:
                raise click.ClickException(f"--args is not valid JSON: {exc}") from exc
            if not isinstance(arguments, dict):
                raise click.ClickException("--args must be a JSON object")
        task = TaskSpec(tool=task_tool, arguments=arguments, source=TaskSource.OPERATOR)

    sandbox_path = sandbox or Path.cwd() / ".arcade-sandbox"
    sandbox_path.mkdir(parents=True, exist_ok=True)

    try:
        receipt = asyncio.run(
            run_bout(
                target=target,
                policy=agent_policy,
                allow_live=allow_live,
                sandbox=sandbox_path,
                n_clean=n_clean,
                task=task,
                wrap=wrap,
                split=split,
                seat=seat,
            )
        )
    except PermissionError as exc:
        raise click.ClickException(str(exc)) from exc
    except DockerError as exc:
        raise click.ClickException(f"docker: {exc}") from exc
    except Exception as exc:
        raise click.ClickException(f"bout failed: {exc}") from exc

    render_preamble(receipt)
    render_timeline(receipt)
    if no_prompt or not sys.stdin.isatty():
        receipt.operator_call.skipped = True
        receipt.operator_call.recorded = False
    else:
        receipt.operator_call = ask_operator_call()
    render_score(receipt)

    if output is not None:
        write_receipt(output, receipt)
        console.print(f"\nReceipt written to {output}")
    else:
        console.print(
            "\n[dim]Pass -o receipt.json to keep the tape. That file is the dataset seed.[/dim]"
        )


@app.command("receipt")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def receipt_cmd(path: Path) -> None:
    """Print a saved receipt as canonical JSON."""
    from mcp_arcade.receipt import read_receipt

    receipt = read_receipt(path)
    click.echo(canonical_dumps(receipt), nl=False)


@app.command("dataset")
@click.argument("receipt_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    "out_dir",
    type=click.Path(path_type=Path),
    required=True,
    help="Directory for train.jsonl, holdout.jsonl and manifest.json.",
)
def dataset_cmd(receipt_dir: Path, out_dir: Path) -> None:
    """Build a dataset from bout receipts. One row per atom, labels from the wire.

    split=proof receipts yield zero rows. Unknown atom ids go to holdout.
    ERROR and SKIP atoms are dropped and tallied, never emitted.
    """
    from mcp_arcade.dataset import DatasetError, build, write

    try:
        result = build(receipt_dir)
        man = write(result, out_dir)
    except DatasetError as exc:
        raise click.ClickException(str(exc)) from exc
    console.print(
        f"rows: train={man['rows']['train']} holdout={man['rows']['holdout']}  "
        f"receipts={len(man['receipts'])}  dropped={man['dropped'] or '{}'}"
    )
    console.print(f"Manifest written to {out_dir / 'manifest.json'}")


@app.group("docker")
def docker_group() -> None:
    """Arcade's own fixture image (built locally from the installed source)."""


@docker_group.command("build-fixture")
def docker_build_fixture() -> None:
    """Build mcp-arcade-fixture:<version> and print its image id."""
    from mcp_arcade import docker as _docker

    try:
        tag, image_id = _docker.build_fixture_image()
    except DockerError as exc:
        raise click.ClickException(f"docker: {exc}") from exc
    click.echo(f"{tag} {image_id}")


@docker_group.command("rm-fixture")
def docker_rm_fixture() -> None:
    """Remove the local fixture image (compensator for build-fixture)."""
    from mcp_arcade import docker as _docker

    click.echo("removed" if _docker.remove_fixture_image() else "nothing to remove")


@docker_group.command("leftovers")
def docker_leftovers() -> None:
    """List arcade-* containers still present (should be none after a bout)."""
    from mcp_arcade import docker as _docker

    names = _docker.leftovers()
    click.echo("\n".join(names) if names else "none")


@app.command("fixture")
def fixture_cmd() -> None:
    """Run the lab MCP server on stdio (used by --target fixture)."""
    from mcp_arcade.fixture import main as fixture_main

    fixture_main()


def main() -> None:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    app()


if __name__ == "__main__":
    main()
