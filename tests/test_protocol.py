"""Framing is the wave-1 seam: NDJSON is the spec, Content-Length is the legacy
dialect, and a message hidden in the *other* dialect under a lock must be a
ProtocolError, never a silent skip (docs/wave-1.md decision 3)."""

from __future__ import annotations

import asyncio
import io
import json

import pytest

from mcp_arcade.protocol import (
    MAX_FRAME_BYTES,
    PROTOCOL_VERSIONS,
    AsyncFrameReader,
    FrameReader,
    Framing,
    FramingSource,
    ProtocolError,
    encode_message,
    is_notification,
    is_request,
    is_response,
    read_message,
    rpc_error,
    rpc_notify,
    rpc_request,
    rpc_result,
    write_message,
)

MULTILINE = {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"text": "a\nb\r\nc"}}


def sync_reader(data: bytes, framing: Framing = Framing.AUTO) -> FrameReader:
    return FrameReader(io.BytesIO(data), framing)


async def async_reader(data: bytes, framing: Framing = Framing.AUTO) -> AsyncFrameReader:
    stream = asyncio.StreamReader()
    stream.feed_data(data)
    stream.feed_eof()
    return AsyncFrameReader(stream, framing)


# ----- versions -----


def test_protocol_versions_latest_first() -> None:
    assert PROTOCOL_VERSIONS[0] == "2025-11-25"
    assert len(set(PROTOCOL_VERSIONS)) == len(PROTOCOL_VERSIONS)


# ----- encoding -----


def test_ndjson_is_the_default_and_ends_with_one_newline() -> None:
    raw = encode_message(rpc_request(1, "tools/list", {}))
    assert raw.endswith(b"\n")
    assert not raw.endswith(b"\n\n")
    assert raw.count(b"\n") == 1
    assert not raw.startswith(b"Content-Length")


def test_ndjson_never_emits_a_raw_newline_from_a_string_field() -> None:
    """The spec: a stdio message MUST NOT contain embedded newlines."""
    raw = encode_message(MULTILINE, Framing.NDJSON)
    body = raw[:-1]
    assert b"\n" not in body
    assert b"\r" not in body
    assert rb"a\nb\r\nc" in body
    assert json.loads(body)["params"]["text"] == "a\nb\r\nc"


def test_content_length_encode_has_the_header() -> None:
    raw = encode_message(rpc_request(1, "tools/list", {}), Framing.CONTENT_LENGTH)
    head, body = raw.split(b"\r\n\r\n", 1)
    assert head.startswith(b"Content-Length: ")
    assert int(head.split(b":", 1)[1]) == len(body)


def test_encode_refuses_auto() -> None:
    with pytest.raises(ProtocolError, match="pick a dialect"):
        encode_message({"jsonrpc": "2.0"}, Framing.AUTO)


def test_write_message_writes_encode_message() -> None:
    msg = rpc_notify("notifications/initialized")
    buf = io.BytesIO()
    write_message(buf, msg, Framing.CONTENT_LENGTH)
    assert buf.getvalue() == encode_message(msg, Framing.CONTENT_LENGTH)


# ----- sync FrameReader -----


@pytest.mark.parametrize("framing", [Framing.NDJSON, Framing.CONTENT_LENGTH])
def test_sync_roundtrip(framing: Framing) -> None:
    msg = rpc_request(1, "initialize", {"protocolVersion": PROTOCOL_VERSIONS[0]})
    buf = io.BytesIO()
    write_message(buf, msg, framing)
    write_message(buf, MULTILINE, framing)
    buf.seek(0)
    reader = FrameReader(buf, framing)
    assert reader.read() == msg
    assert reader.read() == MULTILINE
    assert reader.read() is None
    assert reader.source is FramingSource.FLAG


def test_sync_auto_detects_ndjson() -> None:
    reader = sync_reader(encode_message(rpc_request(1, "ping"), Framing.NDJSON))
    assert reader.read() == rpc_request(1, "ping")
    assert reader.framing is Framing.NDJSON
    assert reader.source is FramingSource.DETECTED


def test_sync_auto_detects_content_length() -> None:
    reader = sync_reader(encode_message(rpc_request(1, "ping"), Framing.CONTENT_LENGTH))
    assert reader.read() == rpc_request(1, "ping")
    assert reader.framing is Framing.CONTENT_LENGTH
    assert reader.source is FramingSource.DETECTED


def test_sync_auto_starts_unsourced() -> None:
    reader = sync_reader(b"")
    assert reader.source is None
    assert reader.read() is None


@pytest.mark.parametrize("framing", [Framing.NDJSON, Framing.CONTENT_LENGTH, Framing.AUTO])
def test_sync_blank_lines_are_skipped(framing: Framing) -> None:
    msg = rpc_result(4, {"tools": []})
    data = b"\n\r\n" + encode_message(msg, Framing.NDJSON if framing is Framing.AUTO else framing)
    reader = FrameReader(io.BytesIO(data), framing)
    assert reader.read() == msg


def test_sync_json_under_content_length_lock_is_an_error() -> None:
    """The smuggling game: a JSON line where a header belongs."""
    data = encode_message(rpc_result(2, {"tools": []}), Framing.NDJSON)
    with pytest.raises(ProtocolError, match="malformed header line"):
        sync_reader(data, Framing.CONTENT_LENGTH).read()


def test_sync_header_under_ndjson_lock_is_an_error() -> None:
    data = encode_message(rpc_result(2, {"tools": []}), Framing.CONTENT_LENGTH)
    with pytest.raises(ProtocolError, match="invalid JSON body"):
        sync_reader(data, Framing.NDJSON).read()


def test_sync_bad_content_length() -> None:
    with pytest.raises(ProtocolError, match="bad Content-Length"):
        sync_reader(b"Content-Length: many\r\n\r\n{}", Framing.CONTENT_LENGTH).read()


def test_sync_missing_content_length() -> None:
    with pytest.raises(ProtocolError, match="missing Content-Length"):
        sync_reader(b"Content-Type: application/json\r\n\r\n{}", Framing.CONTENT_LENGTH).read()


def test_sync_oversized_content_length() -> None:
    header = f"Content-Length: {MAX_FRAME_BYTES + 1}\r\n\r\n".encode("ascii")
    with pytest.raises(ProtocolError, match="out of range"):
        sync_reader(header + b"{}", Framing.CONTENT_LENGTH).read()


def test_sync_negative_content_length() -> None:
    with pytest.raises(ProtocolError, match="out of range"):
        sync_reader(b"Content-Length: -1\r\n\r\n{}", Framing.CONTENT_LENGTH).read()


@pytest.mark.parametrize("body", [b"[1,2]\n", b"12\n", b'"hi"\n', b"null\n"])
def test_sync_non_object_body_is_an_error(body: bytes) -> None:
    with pytest.raises(ProtocolError, match="must be an object"):
        sync_reader(body, Framing.NDJSON).read()


def test_sync_undetectable_first_line() -> None:
    with pytest.raises(ProtocolError, match="cannot detect framing"):
        sync_reader(b"garbage\n").read()


def test_sync_truncated_content_length_body_is_eof_not_error() -> None:
    assert sync_reader(b"Content-Length: 40\r\n\r\n{}", Framing.CONTENT_LENGTH).read() is None


def test_read_message_one_shot() -> None:
    msg = rpc_notify("notifications/message", {"level": "info"})
    assert read_message(io.BytesIO(encode_message(msg))) == msg


# ----- async FrameReader -----


@pytest.mark.parametrize("framing", [Framing.NDJSON, Framing.CONTENT_LENGTH])
async def test_async_roundtrip(framing: Framing) -> None:
    msg = rpc_request(1, "initialize", {"protocolVersion": PROTOCOL_VERSIONS[0]})
    data = encode_message(msg, framing) + encode_message(MULTILINE, framing)
    reader = await async_reader(data, framing)
    assert await reader.read() == msg
    assert await reader.read() == MULTILINE
    assert await reader.read() is None
    assert reader.source is FramingSource.FLAG


async def test_async_auto_detects_ndjson() -> None:
    reader = await async_reader(encode_message(rpc_request(1, "ping"), Framing.NDJSON))
    assert await reader.read() == rpc_request(1, "ping")
    assert reader.framing is Framing.NDJSON
    assert reader.source is FramingSource.DETECTED


async def test_async_auto_detects_content_length() -> None:
    reader = await async_reader(encode_message(rpc_request(1, "ping"), Framing.CONTENT_LENGTH))
    assert await reader.read() == rpc_request(1, "ping")
    assert reader.framing is Framing.CONTENT_LENGTH
    assert reader.source is FramingSource.DETECTED


@pytest.mark.parametrize("framing", [Framing.NDJSON, Framing.CONTENT_LENGTH, Framing.AUTO])
async def test_async_blank_lines_are_skipped(framing: Framing) -> None:
    msg = rpc_result(4, {"tools": []})
    wire = Framing.NDJSON if framing is Framing.AUTO else framing
    reader = await async_reader(b"\n\r\n" + encode_message(msg, wire), framing)
    assert await reader.read() == msg


async def test_async_json_under_content_length_lock_is_an_error() -> None:
    data = encode_message(rpc_result(2, {"tools": []}), Framing.NDJSON)
    reader = await async_reader(data, Framing.CONTENT_LENGTH)
    with pytest.raises(ProtocolError, match="malformed header line"):
        await reader.read()


async def test_async_header_under_ndjson_lock_is_an_error() -> None:
    data = encode_message(rpc_result(2, {"tools": []}), Framing.CONTENT_LENGTH)
    reader = await async_reader(data, Framing.NDJSON)
    with pytest.raises(ProtocolError, match="invalid JSON body"):
        await reader.read()


@pytest.mark.parametrize(
    ("data", "match"),
    [
        (b"Content-Length: many\r\n\r\n{}", "bad Content-Length"),
        (b"Content-Type: application/json\r\n\r\n{}", "missing Content-Length"),
        (f"Content-Length: {MAX_FRAME_BYTES + 1}\r\n\r\n".encode("ascii"), "out of range"),
        (b"Content-Length: -1\r\n\r\n{}", "out of range"),
    ],
)
async def test_async_content_length_header_errors(data: bytes, match: str) -> None:
    reader = await async_reader(data, Framing.CONTENT_LENGTH)
    with pytest.raises(ProtocolError, match=match):
        await reader.read()


@pytest.mark.parametrize("body", [b"[1,2]\n", b"12\n", b'"hi"\n', b"null\n"])
async def test_async_non_object_body_is_an_error(body: bytes) -> None:
    reader = await async_reader(body, Framing.NDJSON)
    with pytest.raises(ProtocolError, match="must be an object"):
        await reader.read()


async def test_async_undetectable_first_line() -> None:
    reader = await async_reader(b"garbage\n")
    with pytest.raises(ProtocolError, match="cannot detect framing"):
        await reader.read()


async def test_async_truncated_body_is_eof_not_error() -> None:
    reader = await async_reader(b"Content-Length: 40\r\n\r\n{}", Framing.CONTENT_LENGTH)
    assert await reader.read() is None


# ----- classification -----


def test_classification() -> None:
    request = rpc_request(1, "tools/list", {})
    notification = rpc_notify("notifications/message", {"level": "info"})
    response = rpc_result(1, {"tools": []})
    error = rpc_error(1, -32601, "nope")

    assert is_request(request) and not is_notification(request) and not is_response(request)
    assert (
        is_notification(notification)
        and not is_request(notification)
        and not is_response(notification)
    )
    assert is_response(response) and not is_request(response) and not is_notification(response)
    assert is_response(error)
    assert error["error"]["code"] == -32601
    # An error with a null id (unparseable request) is still not a request.
    assert not is_request(rpc_error(None, -32700, "parse error"))
