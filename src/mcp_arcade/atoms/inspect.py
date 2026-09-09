"""Atom inspect.tools_list — The Honest Menu.

Hypothesis: tools/list is complete, uniquely named, and a declared tool
can be invoked. We do not score 'looks poisoned'."""

from __future__ import annotations

from mcp_arcade.agent import Task, run_policy
from mcp_arcade.client import McpStdioClient
from mcp_arcade.models import (
    AgentPolicy,
    AtomId,
    AtomResult,
    AtomTitle,
    AxisResult,
    Check,
    ToolInfo,
)

HYPOTHESIS = "the menu the server publishes is the menu the server will serve"


def _smoke_task(tools: list[ToolInfo]) -> Task | None:
    names = {t.name for t in tools}
    if "echo" in names:
        return Task(tool="echo", arguments={"text": "ping"})
    if not tools:
        return None
    # Do not invent required args for unknown servers.
    first = tools[0]
    required = first.input_schema.get("required") if first.input_schema else None
    if required:
        return None
    return Task(tool=first.name, arguments={})


async def run_inspect(client: McpStdioClient, policy: AgentPolicy) -> AtomResult:
    checks: list[Check] = []
    tools = await client.list_tools()
    names = [t.name for t in tools]

    checks.append(
        Check(
            id="nonempty_catalog",
            detail=f"{len(tools)} tool(s) listed",
            result=AxisResult.PASS if tools else AxisResult.FAIL,
        )
    )
    dupes = sorted({n for n in names if names.count(n) > 1})
    checks.append(
        Check(
            id="unique_names",
            detail="duplicate names: " + ",".join(dupes) if dupes else "no duplicate names",
            result=AxisResult.FAIL if dupes else AxisResult.PASS,
        )
    )
    missing_desc = [t.name for t in tools if not t.description.strip()]
    checks.append(
        Check(
            id="descriptions_present",
            detail="missing descriptions: " + ",".join(missing_desc)
            if missing_desc
            else "all described",
            result=AxisResult.FAIL if missing_desc else AxisResult.PASS,
        )
    )

    calls = []
    task = _smoke_task(tools)
    authorized = [task.tool] if task else []
    if task is None:
        checks.append(
            Check(
                id="smoke_invoke",
                detail="no safe smoke task (unknown required args)",
                result=AxisResult.SKIP,
            )
        )
    else:
        calls = await run_policy(client, AgentPolicy.TASK_ONLY, task, tools)
        ok = calls and not calls[0].is_error
        checks.append(
            Check(
                id="smoke_invoke",
                detail=calls[0].result_text[:200] if calls else "no call",
                result=AxisResult.PASS if ok else AxisResult.FAIL,
            )
        )

    hard = [c for c in checks if c.result is AxisResult.FAIL]
    result = AxisResult.FAIL if hard else AxisResult.PASS
    return AtomResult(
        id=AtomId.INSPECT,
        title=AtomTitle.INSPECT.value,
        hypothesis=HYPOTHESIS,
        result=result,
        checks=checks,
        authorized_tools=authorized,
        calls=calls,
        tools_before=tools,
        tools_after=tools,
    )
