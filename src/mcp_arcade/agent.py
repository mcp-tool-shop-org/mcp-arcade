"""Scripted agents. Frozen policies, not LLM judges.

`naive` follows side-quests written into tool descriptions. That is a
known instruction-follower, used to prove the harness measures
follow-through. `task-only` executes the requested tool and stops.

The oracle does not use this parser. It scores the `tools/call` names
that actually went out.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from mcp_arcade.client import McpStdioClient
from mcp_arcade.models import AgentPolicy, ToolCall, ToolInfo

# Frozen. Changing this is a policy change, not an oracle change.
_SIDE_QUEST = re.compile(
    r"also call (?P<name>[A-Za-z0-9_-]+)(?: with (?P<args>\{.*?\}))?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Task:
    tool: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class SideQuest:
    name: str
    arguments: dict[str, Any]


def parse_side_quests(description: str) -> list[SideQuest]:
    found: list[SideQuest] = []
    for match in _SIDE_QUEST.finditer(description):
        args: dict[str, Any] = {}
        raw = match.group("args")
        if raw:
            import json

            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {}
            if isinstance(parsed, dict):
                args = parsed
        found.append(SideQuest(name=match.group("name"), arguments=args))
    return found


async def run_policy(
    client: McpStdioClient,
    policy: AgentPolicy,
    task: Task,
    tools: list[ToolInfo],
) -> list[ToolCall]:
    if policy is AgentPolicy.OLLAMA:
        seat = getattr(client, "seat", None)
        if seat is None:
            raise RuntimeError("ollama policy needs a seat attached to the client")
        # The seat decides every call, including whether the task runs at all.
        # No call at all is utility SKIP downstream, never a pass.
        return await seat.run(client, task.tool, task.arguments, tools)

    calls: list[ToolCall] = []
    calls.append(await client.call_tool(task.tool, task.arguments))
    if policy is AgentPolicy.TASK_ONLY:
        return calls

    by_name = {t.name: t for t in tools}
    listed = by_name.get(task.tool)
    if listed is None:
        return calls
    for quest in parse_side_quests(listed.description):
        if quest.name == task.tool:
            continue
        calls.append(await client.call_tool(quest.name, quest.arguments))
    return calls
