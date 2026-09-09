"""MCP stdio framing (JSON-RPC 2.0 + Content-Length)."""

from __future__ import annotations

import json
from typing import Any, BinaryIO

PROTOCOL_VERSION = "2024-11-05"


class ProtocolError(RuntimeError):
    pass


def encode_message(obj: dict[str, Any]) -> bytes:
    body = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body


def write_message(buf: BinaryIO, obj: dict[str, Any]) -> None:
    buf.write(encode_message(obj))
    buf.flush()


def read_message(buf: BinaryIO) -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = buf.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        try:
            raw = line.decode("ascii", errors="replace").rstrip("\r\n")
        except Exception as exc:
            raise ProtocolError(f"unreadable header: {exc}") from exc
        if ":" not in raw:
            raise ProtocolError(f"malformed header line: {raw!r}")
        key, value = raw.split(":", 1)
        headers[key.strip().lower()] = value.strip()

    length_s = headers.get("content-length")
    if length_s is None:
        raise ProtocolError("missing Content-Length")
    try:
        length = int(length_s)
    except ValueError as exc:
        raise ProtocolError(f"bad Content-Length: {length_s!r}") from exc
    if length < 0 or length > 16 * 1024 * 1024:
        raise ProtocolError(f"Content-Length out of range: {length}")

    body = buf.read(length)
    if len(body) < length:
        return None
    try:
        parsed = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"invalid JSON body: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ProtocolError("JSON-RPC message must be an object")
    return parsed


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
