"""Stdio MCP client that records the wire.

Every JSON-RPC message is appended to `wire` before anyone scores it.
The oracle reads `calls` derived from `tools/call` results, not from
tool descriptions.

Wave 1 shape:

- A background reader demuxes responses by id into futures, so a server
  notification between a request and its response is recorded as an
  observation instead of killing the atom.
- Server-originated requests (sampling, elicitation, roots, ping) are
  recorded, answered with a JSON-RPC error, and listed in
  `server_requests`. Arcade is not a sampling client (C8).
- Per-request timeout. A timeout is a `ClientTimeout`; the atom scores
  ERROR, never attack_success.
- stderr is drained concurrently; the tail lands in `session.stderr_tail`.
- Framing is auto-detected on the first good inbound frame and locked.
  A malformed frame under lock is a ProtocolError, never a skip.
"""

from __future__ import annotations

import asyncio
import os
import shutil
from collections import deque
from typing import Any

from mcp_arcade import __version__
from mcp_arcade.models import (
    AtomId,
    ServerRequest,
    SessionInfo,
    TargetKind,
    TargetSpec,
    ToolCall,
    ToolInfo,
    WireDirection,
    WireEvent,
)
from mcp_arcade.protocol import (
    PROTOCOL_VERSION,
    PROTOCOL_VERSIONS,
    AsyncFrameReader,
    Framing,
    ProtocolError,
    encode_message,
    is_notification,
    is_request,
    is_response,
    rpc_error,
    rpc_notify,
    rpc_request,
)

STDERR_TAIL_BYTES = 4096
_STDERR_KEEP_CHUNKS = 64
_READER_LIMIT = 16 * 1024 * 1024 + 4096


class ClientError(RuntimeError):
    pass


class ClientTimeout(ClientError):
    pass


class RpcError(ClientError):
    """The server answered a request with a JSON-RPC error object."""

    def __init__(self, method: str, error: dict[str, Any]) -> None:
        self.method = method
        self.error = error
        super().__init__(f"{method} error: {error}")


class McpStdioClient:
    def __init__(
        self,
        target: TargetSpec,
        env: dict[str, str] | None = None,
        framing: Framing | str | None = None,
        timeout_s: float | None = None,
    ) -> None:
        self.target = target
        self._extra_env = env or {}
        self.wire: list[WireEvent] = []
        self.server_requests: list[ServerRequest] = []
        self.current_atom: AtomId | None = None
        # Set by the bout: the host fixture, or Arcade's own verified fixture image.
        self.is_fixture: bool = target.kind is TargetKind.FIXTURE
        self.session = SessionInfo()
        self._framing = Framing(framing or target.framing)
        self._timeout = float(timeout_s if timeout_s is not None else target.timeout_s)
        self._proc: asyncio.subprocess.Process | None = None
        self._reader: AsyncFrameReader | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._stderr_task: asyncio.Task[None] | None = None
        self._stderr_chunks: deque[bytes] = deque(maxlen=_STDERR_KEEP_CHUNKS)
        self._pending: dict[int, asyncio.Future[dict[str, Any]]] = {}
        self._id = 0
        self._seq = 0
        self._closed_reason: str | None = None

    # ----- lifecycle -----

    @property
    def started(self) -> bool:
        return self._proc is not None and self._proc.returncode is None

    @property
    def write_framing(self) -> Framing:
        """Dialect we write in. AUTO writes NDJSON (the spec) until the server
        answers, then follows the server."""
        if self._reader is not None and self._reader.framing is not Framing.AUTO:
            return self._reader.framing
        return Framing.NDJSON if self._framing is Framing.AUTO else self._framing

    async def start(self) -> None:
        if not self.target.command:
            raise ClientError("target command is empty")
        env = os.environ.copy()
        env.update(self._extra_env)
        env["PYTHONUNBUFFERED"] = "1"
        argv = list(self.target.command)
        resolved = shutil.which(argv[0])
        if resolved is None and not os.path.exists(argv[0]):
            raise ClientError(
                f"command not found: {argv[0]!r} (not on PATH; on Windows npm shims are .cmd "
                "files, which are resolved via PATHEXT when the name is bare)"
            )
        argv[0] = resolved or argv[0]
        try:
            self._proc = await asyncio.create_subprocess_exec(
                *argv,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.target.cwd,
                env=env,
                limit=_READER_LIMIT,
            )
        except (OSError, ValueError) as exc:
            raise ClientError(f"could not spawn {self.target.command[0]!r}: {exc}") from exc
        if self._proc.stdin is None or self._proc.stdout is None or self._proc.stderr is None:
            raise ClientError("stdio pipes missing")
        self._reader = AsyncFrameReader(self._proc.stdout, self._framing)
        self.session.framing = self._framing.value
        self.session.framing_source = (
            self._reader.source.value if self._reader.source is not None else None
        )
        self._reader_task = asyncio.create_task(self._read_loop(), name="mcp-arcade-reader")
        self._stderr_task = asyncio.create_task(self._stderr_loop(), name="mcp-arcade-stderr")

    async def close(self) -> None:
        proc = self._proc
        self._proc = None
        if proc is None:
            return
        # Spec shutdown: close stdin, wait, SIGTERM, then SIGKILL.
        if proc.stdin is not None and not proc.stdin.is_closing():
            try:
                proc.stdin.close()
            except (OSError, RuntimeError):
                pass
        if proc.returncode is None:
            try:
                await asyncio.wait_for(proc.wait(), timeout=1.5)
            except TimeoutError:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=3)
                except TimeoutError:
                    proc.kill()
                    await proc.wait()
        for task in (self._reader_task, self._stderr_task):
            if task is not None and not task.done():
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
        self._fail_pending(ClientError("client closed"))
        self.session.stderr_tail = self.stderr_tail()

    def stderr_tail(self) -> str:
        data = b"".join(self._stderr_chunks)
        return data[-STDERR_TAIL_BYTES:].decode("utf-8", errors="replace").strip()

    # ----- MCP surface -----

    async def initialize(self) -> dict[str, Any]:
        self.session.protocol_version_sent = PROTOCOL_VERSION
        try:
            result = await self.request(
                "initialize",
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    # Arcade declares no roots, sampling, or elicitation. Anything the
                    # server sends anyway is recorded and rejected.
                    "capabilities": {},
                    "clientInfo": {"name": "mcp-arcade", "version": __version__},
                },
            )
        except ClientError as exc:
            if self._framing is Framing.AUTO and not isinstance(exc, RpcError):
                # Under auto we wrote the spec dialect (NDJSON) first. A server that
                # only reads Content-Length dies on that line. Detection is read-side;
                # there is no wire-compatible hybrid, so say what to do.
                raise ClientError(
                    f"{exc} (framing=auto wrote NDJSON first; if this server only speaks "
                    "Content-Length, rerun with --framing content-length)"
                ) from exc
            raise
        version = result.get("protocolVersion")
        self.session.protocol_version = str(version) if version is not None else None
        info = result.get("serverInfo")
        caps = result.get("capabilities")
        self.session.server_info = info if isinstance(info, dict) else {}
        self.session.server_capabilities = caps if isinstance(caps, dict) else {}
        if version not in PROTOCOL_VERSIONS:
            raise ClientError(
                f"server answered protocolVersion {version!r}; this client speaks "
                f"{', '.join(PROTOCOL_VERSIONS)}"
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
        """A tools/call that the server rejects with a JSON-RPC error is still a
        call that went out on the wire. It is recorded as is_error, not raised."""
        arguments = arguments or {}
        try:
            result = await self.request("tools/call", {"name": name, "arguments": arguments})
        except RpcError as exc:
            return ToolCall(
                name=name,
                arguments=arguments,
                is_error=True,
                result_text=f"jsonrpc error {exc.error.get('code')}: {exc.error.get('message')}",
            )
        is_error = bool(result.get("isError")) if isinstance(result, dict) else True
        text = _content_text(result)
        return ToolCall(name=name, arguments=arguments, is_error=is_error, result_text=text)

    async def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        await self._write(rpc_notify(method, params))

    async def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if self._closed_reason is not None:
            raise ClientError(self._closed_reason)
        self._id += 1
        rpc_id = self._id
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending[rpc_id] = fut
        try:
            await self._write(rpc_request(rpc_id, method, params))
            try:
                message = await asyncio.wait_for(fut, timeout=self._timeout)
            except TimeoutError as exc:
                raise ClientTimeout(
                    f"{method} (id {rpc_id}) got no response in {self._timeout:g}s"
                ) from exc
        finally:
            self._pending.pop(rpc_id, None)
        if "error" in message:
            err = message["error"]
            raise RpcError(method, err if isinstance(err, dict) else {"message": str(err)})
        result = message.get("result")
        if not isinstance(result, dict):
            if result is None:
                return {}
            return {"value": result}
        return result

    # ----- plumbing -----

    async def _write(self, message: dict[str, Any]) -> None:
        if self._proc is None or self._proc.stdin is None:
            raise ClientError("client not started")
        self._record(WireDirection.OUT, message)
        try:
            self._proc.stdin.write(encode_message(message, self.write_framing))
            await self._proc.stdin.drain()
        except (BrokenPipeError, ConnectionResetError, OSError) as exc:
            raise ClientError(f"server closed stdin: {exc}") from exc

    async def _read_loop(self) -> None:
        assert self._reader is not None
        try:
            while True:
                message = await self._reader.read()
                if message is None:
                    tail = self.stderr_tail()
                    self._closed_reason = "server closed stdout" + (f": {tail}" if tail else "")
                    self._fail_pending(ClientError(self._closed_reason))
                    return
                if self._reader.source is not None:
                    self.session.framing = self._reader.framing.value
                    self.session.framing_source = self._reader.source.value
                self._record(WireDirection.IN, message)
                if is_response(message):
                    fut = self._pending.get(_int_id(message.get("id")))
                    if fut is not None and not fut.done():
                        fut.set_result(message)
                    continue
                if is_notification(message):
                    # An observation from the SUT. Recorded; never scored by text.
                    continue
                if is_request(message):
                    await self._reject_server_request(message)
                    continue
                # Neither request, notification, nor response: a malformed envelope.
                raise ProtocolError(f"unclassifiable JSON-RPC message: {list(message)[:6]}")
        except asyncio.CancelledError:
            raise
        except ProtocolError as exc:
            self._closed_reason = f"protocol error: {exc}"
            self._fail_pending(exc)
        except Exception as exc:  # reader must not die silently
            self._closed_reason = f"reader failed: {exc}"
            self._fail_pending(ClientError(self._closed_reason))

    async def _reject_server_request(self, message: dict[str, Any]) -> None:
        method = str(message.get("method"))
        rpc_id = message.get("id")
        self.server_requests.append(
            ServerRequest(
                atom_id=self.current_atom,
                method=method,
                rpc_id=rpc_id if isinstance(rpc_id, (int, str)) else None,
                rejected=True,
            )
        )
        reply = rpc_error(
            rpc_id if isinstance(rpc_id, (int, str)) else None,
            -32601,
            f"mcp-arcade does not serve server-originated requests ({method})",
        )
        try:
            await self._write(reply)
        except ClientError:
            pass

    async def _stderr_loop(self) -> None:
        assert self._proc is not None and self._proc.stderr is not None
        stream = self._proc.stderr
        try:
            while True:
                chunk = await stream.read(4096)
                if not chunk:
                    return
                self._stderr_chunks.append(chunk)
        except asyncio.CancelledError:
            raise
        except Exception:
            return

    def _fail_pending(self, exc: BaseException) -> None:
        for fut in list(self._pending.values()):
            if not fut.done():
                fut.set_exception(exc)
        self._pending.clear()

    def _record(self, direction: WireDirection, message: dict[str, Any]) -> None:
        self._seq += 1
        rpc_id = message.get("id")
        self.wire.append(
            WireEvent(
                seq=self._seq,
                direction=direction,
                method=message.get("method"),
                rpc_id=rpc_id if isinstance(rpc_id, (int, str)) else None,
                message=message,
            )
        )


def _int_id(value: Any) -> int:
    """Our request ids are ints. A server echoing "3" for 3 still gets matched."""
    if isinstance(value, bool):
        return -1
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return -1


def _content_text(result: dict[str, Any]) -> str:
    content = result.get("content")
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            parts.append(str(item.get("text") or ""))
    return "\n".join(parts)
