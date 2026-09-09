"""MCP stdio framing: newline-delimited JSON-RPC (the spec) and Content-Length (LSP-style).

The MCP specification (Transports) says stdio messages are delimited by newlines and
must not contain embedded newlines. Content-Length framing is kept for servers that
speak it. `Framing.AUTO` detects on the first good frame and then locks.

A malformed frame under a locked dialect is a `ProtocolError`, never a silent skip.
That closes the "hide a message in the other dialect" game: the harness errors and the
atom is scored ERROR, not PASS.
"""

from __future__ import annotations

import asyncio
import json
import re
from enum import StrEnum
from typing import Any, BinaryIO

# Handshake-based revisions, latest first. The client sends the first and accepts any
# listed version back. Revision 2026-07-28 replaced the handshake with per-request
# versioning; servers on it still answer `initialize` for these (backward compatibility).
PROTOCOL_VERSIONS: tuple[str, ...] = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
PROTOCOL_VERSION = PROTOCOL_VERSIONS[0]

MAX_FRAME_BYTES = 16 * 1024 * 1024


class ProtocolError(RuntimeError):
    pass


class Framing(StrEnum):
    NDJSON = "ndjson"
    CONTENT_LENGTH = "content-length"
    AUTO = "auto"


class FramingSource(StrEnum):
    FLAG = "flag"
    DETECTED = "detected"


def _dumps(obj: dict[str, Any]) -> bytes:
    # json.dumps escapes newlines inside strings, so the body never contains a raw
    # newline. That is the spec's "MUST NOT contain embedded newlines".
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def encode_message(obj: dict[str, Any], framing: Framing = Framing.NDJSON) -> bytes:
    body = _dumps(obj)
    if framing is Framing.CONTENT_LENGTH:
        return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body
    if framing is Framing.NDJSON:
        return body + b"\n"
    raise ProtocolError("cannot encode with framing=auto; pick a dialect first")


def write_message(buf: BinaryIO, obj: dict[str, Any], framing: Framing = Framing.NDJSON) -> None:
    buf.write(encode_message(obj, framing))
    buf.flush()


def _parse_body(body: bytes) -> dict[str, Any]:
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"invalid JSON body: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ProtocolError("JSON-RPC message must be an object")
    return parsed


_HEADER_KEY = re.compile(r"^[A-Za-z0-9-]+$")


def _parse_header_line(raw: bytes) -> tuple[str, str]:
    text = raw.decode("ascii", errors="replace").rstrip("\r\n")
    if ":" not in text:
        raise ProtocolError(f"malformed header line: {text!r}")
    key, value = text.split(":", 1)
    key = key.strip()
    if not _HEADER_KEY.match(key):
        # A JSON line where a header belongs. Under a Content-Length lock that is
        # a smuggled frame, and it errors now rather than waiting out a timeout.
        raise ProtocolError(f"malformed header line: {text[:80]!r}")
    return key.lower(), value.strip()


def _content_length(headers: dict[str, str]) -> int:
    length_s = headers.get("content-length")
    if length_s is None:
        raise ProtocolError("missing Content-Length")
    try:
        length = int(length_s)
    except ValueError as exc:
        raise ProtocolError(f"bad Content-Length: {length_s!r}") from exc
    if length < 0 or length > MAX_FRAME_BYTES:
        raise ProtocolError(f"Content-Length out of range: {length}")
    return length


def _classify_first_line(line: bytes) -> Framing:
    stripped = line.lstrip()
    if stripped.startswith(b"{"):
        return Framing.NDJSON
    if b":" in line:
        return Framing.CONTENT_LENGTH
    raise ProtocolError(f"cannot detect framing from first line: {line[:80]!r}")


class FrameReader:
    """Synchronous reader over a binary stream (used by the fixture server)."""

    def __init__(self, buf: BinaryIO, framing: Framing = Framing.AUTO) -> None:
        self._buf = buf
        self.framing = framing
        self.source: FramingSource | None = (
            FramingSource.FLAG if framing is not Framing.AUTO else None
        )

    def read(self) -> dict[str, Any] | None:
        while True:
            line = self._buf.readline()
            if not line:
                return None
            if not line.strip():
                # A bare newline is not a message in either dialect; skip it.
                continue
            if self.framing is Framing.AUTO:
                self.framing = _classify_first_line(line)
                self.source = FramingSource.DETECTED
            if self.framing is Framing.NDJSON:
                return _parse_body(line.rstrip(b"\r\n"))
            return self._read_content_length(line)

    def _read_content_length(self, first: bytes) -> dict[str, Any] | None:
        headers: dict[str, str] = {}
        line = first
        while True:
            if line in (b"\r\n", b"\n"):
                break
            key, value = _parse_header_line(line)
            headers[key] = value
            line = self._buf.readline()
            if not line:
                return None
        length = _content_length(headers)
        body = self._buf.read(length)
        if len(body) < length:
            return None
        return _parse_body(body)


class AsyncFrameReader:
    """Async reader over an asyncio.StreamReader (used by the client)."""

    def __init__(self, stream: asyncio.StreamReader, framing: Framing = Framing.AUTO) -> None:
        self._stream = stream
        self.framing = framing
        self.source: FramingSource | None = (
            FramingSource.FLAG if framing is not Framing.AUTO else None
        )

    async def read(self) -> dict[str, Any] | None:
        while True:
            try:
                line = await self._stream.readline()
            except (asyncio.LimitOverrunError, ValueError) as exc:
                raise ProtocolError(f"line too long for framing {self.framing}: {exc}") from exc
            if not line:
                return None
            if not line.strip():
                continue
            if self.framing is Framing.AUTO:
                self.framing = _classify_first_line(line)
                self.source = FramingSource.DETECTED
            if self.framing is Framing.NDJSON:
                return _parse_body(line.rstrip(b"\r\n"))
            return await self._read_content_length(line)

    async def _read_content_length(self, first: bytes) -> dict[str, Any] | None:
        headers: dict[str, str] = {}
        line = first
        while True:
            if line in (b"\r\n", b"\n"):
                break
            key, value = _parse_header_line(line)
            headers[key] = value
            line = await self._stream.readline()
            if not line:
                return None
        length = _content_length(headers)
        try:
            body = await self._stream.readexactly(length)
        except asyncio.IncompleteReadError:
            return None
        return _parse_body(body)


def read_message(buf: BinaryIO, framing: Framing = Framing.AUTO) -> dict[str, Any] | None:
    """One-shot sync read. Tests and simple callers; the fixture keeps a FrameReader."""
    return FrameReader(buf, framing).read()


def rpc_request(rpc_id: int, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    msg: dict[str, Any] = {"jsonrpc": "2.0", "id": rpc_id, "method": method}
    if params is not None:
        msg["params"] = params
    return msg


def rpc_notify(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    return msg


def rpc_result(rpc_id: int | str, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": rpc_id, "result": result}


def rpc_error(rpc_id: int | str | None, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": code, "message": message}}


def is_request(message: dict[str, Any]) -> bool:
    return "method" in message and "id" in message


def is_notification(message: dict[str, Any]) -> bool:
    return "method" in message and "id" not in message


def is_response(message: dict[str, Any]) -> bool:
    return "method" not in message and "id" in message
