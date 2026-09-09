"""Stdio MCP client that records the wire.

Every JSON-RPC message is appended to `wire` before anyone scores it.
The oracle reads `calls` derived from `tools/call` results, not from
tool descriptions.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from mcp_arcade import __version__
from mcp_arcade.models import TargetSpec, ToolCall, ToolInfo, WireDirection, WireEvent
from mcp_arcade.protocol import (
    PROTOCOL_VERSION,
    ProtocolError,
    encode_message,
    rpc_notify,
    rpc_request,
)


class ClientError(RuntimeError):
    pass


class McpStdioClient:
    def __init__(self, target: TargetSpec, env: dict[str, str] | None = None) -> None:
        self.target = target
        self._extra_env = env or {}
        self.wire: list[WireEvent] = []
        self._proc: asyncio.subprocess.Process | None = None
        self._id = 0
        self._seq = 0

    @property
    def started(self) -> bool:
        return self._proc is not None and self._proc.returncode is None

    async def start(self) -> None:
        if not self.target.command:
            raise ClientError("target command is empty")
        env = os.environ.copy()
        env.update(self._extra_env)
        env["PYTHONUNBUFFERED"] = "1"
        self._proc = await asyncio.create_subprocess_exec(
            *self.target.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.target.cwd,
            env=env,
        )
        if self._proc.stdin is None or self._proc.stdout is None:
            raise ClientError("stdio pipes missing")

    async def close(self) -> None:
        proc = self._proc
        self._proc = None
        if proc is None:
            return
        if proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=3)
            except TimeoutError:
                proc.kill()
                await proc.wait()

    async def initialize(self) -> dict[str, Any]:
        result = await self.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "mcp-arcade", "version": __version__},
            },
        )
        await self.notify("notifications/initialized")
        return result

    async def list_tools(self) -> list[ToolInfo]:
        result = await self.request("tools/list", {})
        tools = result.get("tools") if isinstance(result, dict) else None
        if not isinstance(tools, list):
            raise ClientError("tools/list did not return tools[]")
        out: list[ToolInfo] = []
        for raw in tools:
            if not isinstance(raw, dict) or "name" not in raw:
                continue
            schema = raw.get("inputSchema") or raw.get("input_schema") or {}
            if not isinstance(schema, dict):
                schema = {}
            out.append(
                ToolInfo(
                    name=str(raw["name"]),
                    description=str(raw.get("description") or ""),
                    input_schema=schema,
                )
            )
        return out

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> ToolCall:
        arguments = arguments or {}
        result = await self.request("tools/call", {"name": name, "arguments": arguments})
        is_error = bool(result.get("isError")) if isinstance(result, dict) else True
        text = _content_text(result)
        return ToolCall(name=name, arguments=arguments, is_error=is_error, result_text=text)

    async def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        await self._write(rpc_notify(method, params), direction=WireDirection.OUT)

    async def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._id += 1
        rpc_id = self._id
        await self._write(rpc_request(rpc_id, method, params), direction=WireDirection.OUT)
        message = await self._read()
        if message.get("id") != rpc_id:
            raise ClientError(f"id mismatch: sent {rpc_id}, got {message.get('id')}")
        if "error" in message:
            err = message["error"]
            raise ClientError(f"{method} error: {err}")
        result = message.get("result")
        if not isinstance(result, dict):
            # tools/call result is a dict; initialize too. Allow empty.
            if result is None:
                return {}
            return {"value": result}
        return result

    async def _write(self, message: dict[str, Any], direction: WireDirection) -> None:
        if self._proc is None or self._proc.stdin is None:
            raise ClientError("client not started")
        self._record(direction, message)
        self._proc.stdin.write(encode_message(message))
        await self._proc.stdin.drain()

    async def _read(self) -> dict[str, Any]:
        if self._proc is None or self._proc.stdout is None:
            raise ClientError("client not started")
        headers = await self._read_headers()
        length_s = headers.get("content-length")
        if length_s is None:
            raise ProtocolError("missing Content-Length from server")
        length = int(length_s)
        body = await self._proc.stdout.readexactly(length)
        import json

        message = json.loads(body.decode("utf-8"))
        if not isinstance(message, dict):
            raise ProtocolError("server sent non-object JSON")
        self._record(WireDirection.IN, message)
        return message

    async def _read_headers(self) -> dict[str, str]:
        assert self._proc is not None and self._proc.stdout is not None
        headers: dict[str, str] = {}
        while True:
            line = await self._proc.stdout.readline()
            if not line:
                stderr = await self._drain_stderr()
                raise ClientError(f"server closed stdout{': ' + stderr if stderr else ''}")
            if line in (b"\r\n", b"\n"):
                return headers
            raw = line.decode("ascii", errors="replace").rstrip("\r\n")
            if ":" not in raw:
                continue
            key, value = raw.split(":", 1)
            headers[key.strip().lower()] = value.strip()

    async def _drain_stderr(self) -> str:
        if self._proc is None or self._proc.stderr is None:
            return ""
        try:
            data = await asyncio.wait_for(self._proc.stderr.read(4096), timeout=0.2)
        except TimeoutError:
            return ""
        return data.decode("utf-8", errors="replace").strip()

    def _record(self, direction: WireDirection, message: dict[str, Any]) -> None:
        self._seq += 1
        self.wire.append(
            WireEvent(
                seq=self._seq,
                direction=direction,
                method=message.get("method"),
                rpc_id=message.get("id"),
                message=message,
            )
        )


def _content_text(result: dict[str, Any]) -> str:
    content = result.get("content")
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            parts.append(str(item.get("text") or ""))
    return "\n".join(parts)
