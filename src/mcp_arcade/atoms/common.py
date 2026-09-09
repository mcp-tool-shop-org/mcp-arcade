"""Shared atom helpers: the named task and the fail-closed default."""

from __future__ import annotations

from mcp_arcade.agent import Task
from mcp_arcade.models import TaskSource, TaskSpec, ToolInfo

FIXTURE_TASKS: dict[str, dict[str, str]] = {
    "echo": {"text": "ping"},
}


def resolve_task(tools: list[ToolInfo], requested: TaskSpec | None, text: str) -> TaskSpec:
    """Pick the benign task for an atom.

    Operator-named wins and is recorded as such. Otherwise `echo` (the fixture
    default) if the server lists it. Otherwise no task: the atom SKIPs rather
    than inventing arguments for a tool it does not understand.
    """
    if requested is not None and requested.tool:
        return TaskSpec(
            tool=requested.tool, arguments=dict(requested.arguments), source=TaskSource.OPERATOR
        )
    names = {t.name for t in tools}
    if "echo" in names:
        return TaskSpec(tool="echo", arguments={"text": text}, source=TaskSource.FIXTURE_DEFAULT)
    return TaskSpec()


def as_task(spec: TaskSpec) -> Task | None:
    if not spec.tool:
        return None
    return Task(tool=spec.tool, arguments=dict(spec.arguments))
