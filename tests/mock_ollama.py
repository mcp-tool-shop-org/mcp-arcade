"""A mock Ollama `/api/chat` server for the seat tests.

The real seat talks to a GPU that other sessions share, so no test in this
repo may call it. This is the stand-in: a threading HTTP server on an
ephemeral 127.0.0.1 port that answers `POST /api/chat` from a scripted
queue and records every request body it was sent.

Two things make it useful beyond "it returns something":

- `requests` is the tape of what Arcade *sent* the model. The prompt-
  invariance and notification tests read it, so a side channel added to
  `build_messages` would show up here.
- Once the queue is exhausted the mock answers with a message carrying no
  `tool_calls`, which is the seat's stop condition. A test only scripts
  the turns it cares about.
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from mcp_arcade.seat import SeatConfig

MODEL = "mockmodel"


def assistant(
    calls: Iterable[tuple[str, dict[str, Any]]] = (),
    content: str = "",
    thinking: str = "",
    *,
    raw_calls: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """One Ollama chat response. `content` and `thinking` are the model text the
    seat must never carry anywhere."""
    message: dict[str, Any] = {"role": "assistant", "content": content}
    if thinking:
        message["thinking"] = thinking
    tool_calls = (
        raw_calls
        if raw_calls is not None
        else [{"function": {"name": name, "arguments": args}} for name, args in calls]
    )
    if tool_calls:
        message["tool_calls"] = tool_calls
    return {"model": MODEL, "created_at": "2026-09-09T00:00:00Z", "message": message, "done": True}


def stop(content: str = "done") -> dict[str, Any]:
    """A turn with no tool calls: the seat's stop."""
    return assistant(content=content)


class MockOllama:
    def __init__(self, script: list[dict[str, Any]] | None = None) -> None:
        self.script: list[dict[str, Any]] = list(script or [])
        self.requests: list[dict[str, Any]] = []
        self.status = 200
        self.delay = 0.0
        self.body_override: bytes | None = None
        self._lock = threading.Lock()
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    # ----- lifecycle -----

    def start(self) -> None:
        mock = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def do_POST(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler API)
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length)
                try:
                    body = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    body = {"_unparseable": True}
                mock._record(self.path, body)
                if mock.delay:
                    time.sleep(mock.delay)
                status, payload = mock._answer()
                try:
                    self.send_response(status)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except OSError:
                    # The seat timed out and hung up. Not the mock's problem.
                    pass

            def log_message(self, *args: Any) -> None:
                return

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._server.daemon_threads = True
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def close(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    # ----- the tape -----

    def _record(self, path: str, body: dict[str, Any]) -> None:
        with self._lock:
            self.requests.append({"path": path, "body": body})

    def _answer(self) -> tuple[int, bytes]:
        if self.body_override is not None:
            return self.status, self.body_override
        with self._lock:
            response = self.script.pop(0) if self.script else stop()
        if self.status != 200:
            return self.status, json.dumps({"error": "mock ollama failure"}).encode("utf-8")
        return 200, json.dumps(response).encode("utf-8")

    @property
    def endpoint(self) -> str:
        assert self._server is not None, "mock ollama not started"
        return f"http://127.0.0.1:{self._server.server_address[1]}"

    @property
    def bodies(self) -> list[dict[str, Any]]:
        with self._lock:
            return [r["body"] for r in self.requests]

    def messages(self, index: int) -> list[dict[str, Any]]:
        return list(self.bodies[index].get("messages") or [])

    def seat_config(self, model: str = MODEL, **overrides: Any) -> SeatConfig:
        kwargs: dict[str, Any] = {"endpoint": self.endpoint, "timeout_s": 5.0}
        kwargs.update(overrides)
        return SeatConfig(model=model, **kwargs)


@contextmanager
def mock_ollama(script: list[dict[str, Any]] | None = None) -> Iterator[MockOllama]:
    mock = MockOllama(script)
    mock.start()
    try:
        yield mock
    finally:
        mock.close()
