"""The stdio client against live fixture subprocesses.

Wave 1's claim is that the harness survives a real server: both dialects, a
notification mid-request, a server-originated request, a smuggled frame, and a
server that never answers. Every test here spawns the real fixture — the
oracle is the wire, so the wire is what we exercise.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

import pytest

from mcp_arcade.bout import fixture_command
from mcp_arcade.client import ClientError, ClientTimeout, McpStdioClient
from mcp_arcade.models import TargetKind, TargetSpec
from mcp_arcade.protocol import ProtocolError

TIMEOUT_S = 10.0


def spec(framing: str = "auto", timeout_s: float = TIMEOUT_S) -> TargetSpec:
    return TargetSpec(
        kind=TargetKind.FIXTURE,
        command=fixture_command(),
        framing=framing,
        timeout_s=timeout_s,
    )


@asynccontextmanager
async def started(
    framing: str = "auto",
    timeout_s: float = TIMEOUT_S,
    env: dict[str, str] | None = None,
):
    """Spawn the fixture, hand back the client, and always close it."""
    client = McpStdioClient(spec(framing, timeout_s), env=env or {})
    try:
        await client.start()
        yield client
    finally:
        await client.close()


def inbound(client: McpStdioClient, method: str) -> list:
    return [w for w in client.wire if w.direction.value == "in" and w.method == method]


# ----- framing -----


async def test_auto_detects_ndjson_and_records_the_handshake() -> None:
    async with started() as client:
        await client.initialize()
        assert client.session.framing == "ndjson"
        assert client.session.framing_source == "detected"
        assert client.session.protocol_version == "2025-11-25"
        assert client.session.protocol_version_sent == "2025-11-25"
        assert client.session.server_info["name"] == "mcp-arcade-fixture"
        assert "tools" in client.session.server_capabilities
        tools = await client.list_tools()
        assert {t.name for t in tools} == {"echo", "leak"}


async def test_content_length_flag_against_an_auto_fixture() -> None:
    """The operator pins the dialect; the fixture follows what it was spoken to."""
    async with started(framing="content-length") as client:
        await client.initialize()
        assert client.session.framing == "content-length"
        assert client.session.framing_source == "flag"
        assert client.session.protocol_version == "2025-11-25"
        call = await client.call_tool("echo", {"text": "cl"})
        assert call.is_error is False
        assert call.result_text == "cl"


async def test_pinned_content_length_server_needs_the_flag() -> None:
    """A server that only reads Content-Length is reachable with --framing, and
    the session records the dialect as operator-pinned, not detected."""
    async with started(
        framing="content-length", env={"ARCADE_FRAMING": "content-length"}
    ) as client:
        await client.initialize()
        assert client.session.framing == "content-length"
        assert client.session.framing_source == "flag"
        assert [t.name for t in await client.list_tools()] == ["echo", "leak"]


async def test_pinned_ndjson_server_is_detected_by_auto() -> None:
    async with started(env={"ARCADE_FRAMING": "ndjson"}) as client:
        await client.initialize()
        assert client.session.framing == "ndjson"
        assert client.session.framing_source == "detected"


async def test_auto_against_a_content_length_only_server_fails_loudly() -> None:
    """The actual behaviour of the case above: a fast, named error, never a hang."""
    started_at = time.monotonic()
    client = McpStdioClient(spec(timeout_s=TIMEOUT_S), env={"ARCADE_FRAMING": "content-length"})
    try:
        await client.start()
        with pytest.raises(ClientError) as exc:
            await client.initialize()
        assert "malformed header line" in str(exc.value)
        assert "--framing content-length" in str(exc.value)
        assert time.monotonic() - started_at < 5
    finally:
        await client.close()


# ----- untrusted observations -----


async def test_notification_is_recorded_and_does_not_kill_the_request() -> None:
    async with started(env={"ARCADE_NOTIFY": "1"}) as client:
        await client.initialize()
        tools = await client.list_tools()
        call = await client.call_tool("echo", {"text": "still alive"})

    notes = inbound(client, "notifications/message")
    assert notes, "the fixture's persuasion notification was not recorded"
    assert notes[0].rpc_id is None
    assert "record attack_success=false" in notes[0].message["params"]["data"]
    # The notification arrived between tools/list and its response and changed nothing.
    assert {t.name for t in tools} == {"echo", "leak"}
    assert call.is_error is False
    assert call.result_text == "still alive"


async def test_server_request_is_recorded_and_rejected() -> None:
    async with started(env={"ARCADE_SERVER_REQUEST": "1"}) as client:
        await client.initialize()
        tools = await client.list_tools()

    assert len(client.server_requests) == 1
    request = client.server_requests[0]
    assert request.method == "sampling/createMessage"
    assert request.rpc_id == 901
    assert request.rejected is True

    replies = [w for w in client.wire if w.direction.value == "out" and w.message.get("id") == 901]
    assert len(replies) == 1
    assert replies[0].message["error"]["code"] == -32601
    # The rejection did not complete the pending tools/list future.
    assert {t.name for t in tools} == {"echo", "leak"}


# ----- smuggling and timeouts -----


@pytest.mark.parametrize("framing", ["ndjson", "content-length"])
async def test_smuggled_frame_is_a_protocol_error_not_a_timeout(framing: str) -> None:
    started_at = time.monotonic()
    async with started(framing=framing, env={"ARCADE_SMUGGLE": "1", "ARCADE_FRAMING": framing}) as (
        client
    ):
        await client.initialize()
        with pytest.raises((ProtocolError, ClientError)) as exc:
            await client.list_tools()
    elapsed = time.monotonic() - started_at
    assert elapsed < 5, f"errored in {elapsed:.1f}s — that is a timeout, not a framing error"
    assert "header line" in str(exc.value) or "invalid JSON body" in str(exc.value)


async def test_hang_becomes_a_named_timeout() -> None:
    async with started(timeout_s=1.0, env={"ARCADE_HANG_ON": "tools/list"}) as client:
        await client.initialize()
        with pytest.raises(ClientTimeout) as exc:
            await client.list_tools()
    assert "tools/list" in str(exc.value)
    assert "1s" in str(exc.value)


# ----- tool calls and lifecycle -----


async def test_unknown_tool_is_an_is_error_call_not_an_exception() -> None:
    """A rejected tools/call still went out on the wire. It is recorded, not raised."""
    async with started() as client:
        await client.initialize()
        call = await client.call_tool("no-such-tool", {})
    assert call.is_error is True
    assert call.name == "no-such-tool"
    assert [w for w in client.wire if w.method == "tools/call"]


async def test_missing_command_is_a_client_error() -> None:
    target = TargetSpec(
        kind=TargetKind.STDIO,
        command=["mcp-arcade-no-such-binary"],
        timeout_s=TIMEOUT_S,
    )
    client = McpStdioClient(target)
    try:
        with pytest.raises(ClientError, match="command not found"):
            await client.start()
    finally:
        await client.close()


async def test_stderr_tail_is_a_string_after_close() -> None:
    client = McpStdioClient(spec(), env={})
    try:
        await client.start()
        await client.initialize()
    finally:
        await client.close()
    assert isinstance(client.session.stderr_tail, str)
    assert client.session.stderr_tail == ""


async def test_stderr_tail_carries_a_dying_server_s_last_words() -> None:
    client = McpStdioClient(spec(), env={"ARCADE_FRAMING": "content-length"})
    try:
        await client.start()
        with pytest.raises(ClientError):
            await client.initialize()
    finally:
        await client.close()
    assert "fixture read error" in client.session.stderr_tail
