import io
import json

from mcp_arcade.protocol import encode_message, read_message, rpc_request, write_message


def test_roundtrip_content_length() -> None:
    msg = rpc_request(1, "initialize", {"protocolVersion": "2024-11-05"})
    buf = io.BytesIO()
    write_message(buf, msg)
    buf.seek(0)
    got = read_message(buf)
    assert got == json.loads(encode_message(msg).split(b"\r\n\r\n", 1)[1])
    assert got["method"] == "initialize"
    assert got["id"] == 1


def test_encode_has_header() -> None:
    raw = encode_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert raw.startswith(b"Content-Length:")
    assert b"\r\n\r\n" in raw
