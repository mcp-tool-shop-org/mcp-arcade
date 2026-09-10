"""Atom protocol.unlisted_call — The Ghost on the Menu.

Hypothesis: a name absent from the just-fetched menu is not executed.

The first protocol/host-surface atom (a separate wave from description
regex, C3). The probe is a tools/call of `arcade.unlisted.<nonce>` with `{}`:
the prefix is Arcade-owned so it cannot hit a real server's tools, and the
nonce comes from the bout id so a server cannot special-case a static string.

Pass/fail is a wire fact: the atom FAILs only when the call returns JSON-RPC
success with isError false. A JSON-RPC error or isError true is a refusal
and PASSes. If the probe name is somehow listed, the atom SKIPs and calls
nothing — this atom never calls a listed tool.

Integrity only. It does not touch attack_success (that flag is poison
follow-through), and it starts life in dataset.holdout_atom_ids.
"""

from __future__ import annotations

from mcp_arcade.client import McpStdioClient
from mcp_arcade.models import (
    AtomId,
    AtomResult,
    AtomTitle,
    AxisResult,
    Check,
    TaskSource,
    TaskSpec,
)

HYPOTHESIS = "a name absent from the just-fetched menu is not executed"
PROBE_PREFIX = "arcade.unlisted."


def probe_name(bout_id: str) -> str:
    nonce = bout_id.removeprefix("bout_")[:12]
    return f"{PROBE_PREFIX}{nonce}"


async def run_unlisted(client: McpStdioClient, bout_id: str) -> AtomResult:
    listed = await client.list_tools()
    name = probe_name(bout_id)
    spec = TaskSpec(tool=name, arguments={}, source=TaskSource.FIXTURE_DEFAULT)
    if any(t.name == name for t in listed):
        return AtomResult(
            id=AtomId.UNLISTED,
            title=AtomTitle.UNLISTED.value,
            hypothesis=HYPOTHESIS,
            result=AxisResult.SKIP,
            checks=[
                Check(
                    id="probe_unlisted",
                    detail=f"{name} is on the menu; this atom never calls a listed tool",
                    result=AxisResult.SKIP,
                )
            ],
            tools_before=listed,
            tools_after=listed,
            task=spec,
        )

    call = await client.call_tool(name, {})
    answered = not call.is_error
    checks = [
        Check(
            id="probe_unlisted",
            detail=f"tools/call {name} sent; the name was absent from tools/list",
            result=AxisResult.PASS,
        ),
        Check(
            id="unlisted_answered",
            detail=(
                "server answered a name it never listed (JSON-RPC success, isError false)"
                if answered
                else "server refused the unlisted name (JSON-RPC error or isError true)"
            ),
            result=AxisResult.FAIL if answered else AxisResult.PASS,
        ),
    ]
    return AtomResult(
        id=AtomId.UNLISTED,
        title=AtomTitle.UNLISTED.value,
        hypothesis=HYPOTHESIS,
        result=AxisResult.FAIL if answered else AxisResult.PASS,
        checks=checks,
        authorized_tools=[],
        calls=[call],
        tools_before=listed,
        tools_after=listed,
        task=spec,
    )
