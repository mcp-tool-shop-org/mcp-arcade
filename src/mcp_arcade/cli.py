"""CLI. Fail-closed: no target, no bout."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console

from mcp_arcade import __version__
from mcp_arcade.bout import resolve_target, run_bout
from mcp_arcade.models import AgentPolicy, AtomTitle
from mcp_arcade.receipt import canonical_dumps, write_receipt
from mcp_arcade.tui import ask_operator_call, render_preamble, render_score, render_timeline

console = Console()


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
    type=click.Choice(["fixture", "stdio"]),
    required=True,
    help="fixture = lab server. stdio = your command (needs --allow-live).",
)
@click.option(
    "--cmd",
    "command",
    multiple=True,
    help="stdio argv, repeatable. Example: --cmd python --cmd -m --cmd my_server",
)
@click.option(
    "--agent",
    "policy",
    type=click.Choice([p.value for p in AgentPolicy]),
    default=AgentPolicy.NAIVE.value,
    show_default=True,
    help="naive follows description side-quests. task-only does not.",
)
@click.option("--allow-live", is_flag=True, help="Required for non-fixture targets.")
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
    policy: str,
    allow_live: bool,
    no_prompt: bool,
    output: Path | None,
    sandbox: Path | None,
    n_clean: int,
) -> None:
    """Run the three v0 atoms and print a contrastive house call."""
    try:
        target = resolve_target(target_kind, list(command) if command else None)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    sandbox_path = sandbox or Path.cwd() / ".arcade-sandbox"
    sandbox_path.mkdir(parents=True, exist_ok=True)

    try:
        receipt = asyncio.run(
            run_bout(
                target=target,
                policy=AgentPolicy(policy),
                allow_live=allow_live,
                sandbox=sandbox_path,
                n_clean=n_clean,
            )
        )
    except PermissionError as exc:
        raise click.ClickException(str(exc)) from exc
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
