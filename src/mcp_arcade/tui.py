"""Rich TUI. Humor is second. The score is delayed until you call it."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from mcp_arcade.models import BoutReceipt, OperatorCall

console = Console()


def render_preamble(receipt: BoutReceipt) -> None:
    console.print(
        Panel.fit(
            "[bold]MCP Arcade[/bold] — GameDay, not a high score\n"
            "[dim]The house keeps the tape. The bar is not a safety certificate.[/dim]",
            border_style="cyan",
        )
    )
    console.print(
        f"Bout [cyan]{receipt.bout_id}[/cyan]  target={receipt.target.kind.value}  "
        f"policy={receipt.agent_policy.value}"
    )
    console.print(f"[dim]Hypothesis:[/dim] {receipt.hypothesis}\n")


def render_timeline(receipt: BoutReceipt) -> None:
    table = Table(title="Waves (atoms)", show_header=True)
    table.add_column("Atom", style="yellow")
    table.add_column("Title")
    table.add_column("Calls")
    table.add_column("Notes", overflow="fold")
    for atom in receipt.atoms:
        calls = ", ".join(c.name for c in atom.calls) or "—"
        table.add_row(atom.id.value, atom.title, calls, "; ".join(atom.notes[:2]) or "—")
    console.print(table)
    console.print()


def ask_operator_call() -> OperatorCall:
    console.print(
        "[bold]Before the house posts the score[/bold] — what do you think the wire will show?"
    )
    guess = Prompt.ask(
        "followed / held / unclear",
        choices=["followed", "held", "unclear"],
        default="unclear",
    )
    return OperatorCall(recorded=True, guess=guess, skipped=False)  # type: ignore[arg-type]


def render_score(receipt: BoutReceipt) -> None:
    s = receipt.scores
    console.print(
        Panel(
            f"[bold]Integrity[/bold] {s.integrity.value}   "
            f"[bold]Utility[/bold] {s.utility.value}   "
            f"[bold]NRP[/bold] {s.nrp:.2f}\n"
            f"task_success={s.task_success}  attack_success={s.attack_success}\n\n"
            f"[yellow]Foil.[/yellow] {receipt.contrastive.foil}\n"
            f"[cyan]Wire.[/cyan] {receipt.contrastive.wire}",
            title="House call (not a certificate)",
            border_style="magenta",
        )
    )
    for atom in receipt.atoms:
        console.print(
            f"\n[bold]{atom.title}[/bold] [dim]{atom.id.value}[/dim] → {atom.result.value}"
        )
        for check in atom.checks:
            mark = {"pass": "·", "fail": "×", "skip": "–", "error": "!"}.get(
                check.result.value, "?"
            )
            console.print(f"  {mark} {check.id}: {check.detail}")
