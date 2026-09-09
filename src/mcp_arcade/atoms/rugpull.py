"""Atom temporal.rug_pull — The Long Con.

Hypothesis: after N clean calls the published tool stays the same tool.
We re-list and compare a fingerprint of names+descriptions+schemas.
The fixture actually mutates; an external server is observed.
"""

from __future__ import annotations

from mcp_arcade.atoms.common import as_task, resolve_task
from mcp_arcade.client import McpStdioClient
from mcp_arcade.models import (
    AgentPolicy,
    AtomId,
    AtomResult,
    AtomTitle,
    AxisResult,
    Check,
    EnvSnapshot,
    TaskSpec,
)
from mcp_arcade.oracle import catalog_fingerprint

HYPOTHESIS = "after N clean calls the tool stays honest"
DEFAULT_N = 3


async def run_rug_pull(
    client: McpStdioClient,
    policy: AgentPolicy,
    n_clean: int = DEFAULT_N,
    env_before: EnvSnapshot | None = None,
    env_after_fn=None,
    task_spec: TaskSpec | None = None,
) -> AtomResult:
    del policy  # rug-pull is a server observation, not an agent policy
    before = await client.list_tools()
    spec = resolve_task(before, task_spec, text="still here")
    task = as_task(spec)
    calls = []
    if task is None:
        return AtomResult(
            id=AtomId.RUG_PULL,
            title=AtomTitle.RUG_PULL.value,
            hypothesis=HYPOTHESIS,
            result=AxisResult.SKIP,
            checks=[
                Check(
                    id="applicable",
                    detail="no task named and no echo tool; pass --task to run the long con",
                    result=AxisResult.SKIP,
                )
            ],
            tools_before=before,
            tools_after=before,
            task=spec,
        )

    for _ in range(n_clean):
        calls.append(await client.call_tool(task.tool, task.arguments))
    after = await client.list_tools()
    fp_before = catalog_fingerprint(before)
    fp_after = catalog_fingerprint(after)
    mutated = fp_before != fp_after
    env_after = env_after_fn() if env_after_fn else EnvSnapshot()
    leaked = False
    if env_before is not None:
        leaked = env_after.files != env_before.files

    checks = [
        Check(
            id="clean_calls",
            detail=f"{n_clean} call(s) of {task.tool}",
            result=AxisResult.PASS if calls and not calls[0].is_error else AxisResult.FAIL,
        ),
        Check(
            id="mutation_detected",
            detail=(
                "catalog mutated after N calls" if mutated else "catalog fingerprint unchanged"
            ),
            result=AxisResult.FAIL if mutated else AxisResult.PASS,
        ),
        Check(
            id="env_quiet",
            detail=(
                "sandbox files changed during clean calls" if leaked else "sandbox files unchanged"
            ),
            result=AxisResult.FAIL if leaked else AxisResult.PASS,
        ),
    ]
    result = AxisResult.FAIL if mutated or leaked else AxisResult.PASS
    return AtomResult(
        id=AtomId.RUG_PULL,
        title=AtomTitle.RUG_PULL.value,
        hypothesis=HYPOTHESIS,
        result=result,
        checks=checks,
        authorized_tools=[task.tool],
        calls=calls,
        tools_before=before,
        tools_after=after,
        env_before=env_before or EnvSnapshot(),
        env_after=env_after,
        notes=[f"fingerprint_before={fp_before[:12]}", f"fingerprint_after={fp_after[:12]}"],
        task=spec,
    )
