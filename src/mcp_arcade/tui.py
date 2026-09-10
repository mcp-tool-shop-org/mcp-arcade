"""Rich TUI. Humor is second. The score is delayed until you call it.

Anything the server said (notifications, server-originated requests) is
printed as SUT wire, in the server's words, never in Arcade's voice.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from mcp_arcade.models import BoutReceipt, OperatorCall
from mcp_arcade.oracle import server_notifications

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
    sessions = [a.session for a in receipt.atoms if a.session.protocol_version]
    if sessions:
        s = sessions[0]
        name = s.server_info.get("name", "?")
        ver = s.server_info.get("version", "?")
        console.print(
            f"[dim]Server:[/dim] {name} {ver}  [dim]protocol[/dim] {s.protocol_version}  "
            f"[dim]framing[/dim] {s.framing} ({s.framing_source or 'unknown'})"
        )
    containers = [a.session.container for a in receipt.atoms if a.session.container]
    if containers:
        c = containers[0]
        console.print(
            f"[dim]Container:[/dim] {c.image} [dim]{c.image_id[:19]}[/dim]  "
            f"[dim]fixture_image[/dim]={c.fixture_image}  [dim]binds[/dim]={c.bind_requested}"
        )
    seats = [a.session.seat for a in receipt.atoms if a.session.seat]
    if seats:
        s = seats[0]
        console.print(
            f"[dim]Seat:[/dim] ollama {s.model}  t={s.temperature} seed={s.seed} "
            f"num_ctx={s.num_ctx}  [dim]template[/dim] {s.prompt_template_sha256[:12]}"
        )
    if receipt.task.tool:
        console.print(
            f"[dim]Task:[/dim] {receipt.task.tool} {receipt.task.arguments} "
            f"[dim]({receipt.task.source.value})[/dim]"
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

    said = server_notifications(receipt.wire)
    if said or receipt.server_requests:
        table = Table(title="Server said (untrusted wire, not scored)", show_header=True)
        table.add_column("Kind", style="magenta")
        table.add_column("Method")
        table.add_column("Payload", overflow="fold")
        for event in said:
            params = event.message.get("params")
            payload = str(params.get("data", params)) if isinstance(params, dict) else ""
            table.add_row("notification", event.method or "?", payload[:160])
        for req in receipt.server_requests:
            table.add_row(
                "request",
                req.method,
                f"id={req.rpc_id} atom={req.atom_id.value if req.atom_id else '?'} "
                f"{'rejected' if req.rejected else 'served'}",
            )
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
        if atom.session.stderr_tail:
            tail = atom.session.stderr_tail.splitlines()[-3:]
            console.print("  [dim]stderr tail:[/dim] " + " | ".join(tail)[:240])
