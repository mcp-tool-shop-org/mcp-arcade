"""Golden-receipt helpers.

A receipt is the dataset seed, so a regression in the oracle or the harness
should fail a diff, not a vibe check. Two functions do that job:

`normalize` strips what is volatile per run (ids, clocks, the interpreter
path, package versions, the stderr tail) and keeps everything else, so the
committed file stays readable by a human.

`projection` keeps only the fields we actually assert on: the scores, the
atom shape, the wire *shape* (not payloads), and the server requests.
Contrastive prose and check details are deliberately excluded — they are
operator copy, and copy edits must not turn into red tests.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).parent / "fixtures"

GOLDEN_COMMAND = ["<python>", "-m", "mcp_arcade.fixture"]
GOLDEN_BOUT_ID = "bout_GOLDEN"
GOLDEN_STAMP = "GOLDEN"
GOLDEN_VERSION = "<version>"


def _scrub_versions(node: Any) -> None:
    """Any clientInfo/serverInfo block, wherever it sits on the tape."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ("clientInfo", "serverInfo") and isinstance(value, dict):
                if "version" in value:
                    value["version"] = GOLDEN_VERSION
            _scrub_versions(value)
    elif isinstance(node, list):
        for item in node:
            _scrub_versions(item)


def normalize(receipt: dict[str, Any]) -> dict[str, Any]:
    """Deep-copy `receipt` with the per-run facts replaced by fixed markers."""
    out = copy.deepcopy(receipt)
    out["bout_id"] = GOLDEN_BOUT_ID
    out["started_at"] = GOLDEN_STAMP
    out["finished_at"] = GOLDEN_STAMP
    out["target"]["command"] = list(GOLDEN_COMMAND)
    for atom in out.get("atoms", []):
        session = atom.get("session")
        if isinstance(session, dict):
            session["stderr_tail"] = ""
            server_info = session.get("server_info")
            if isinstance(server_info, dict) and "version" in server_info:
                server_info["version"] = GOLDEN_VERSION
    _scrub_versions(out.get("wire", []))
    return out


def projection(receipt: dict[str, Any]) -> dict[str, Any]:
    """The diffable core of a receipt: scores, atom shape, wire shape."""
    return {
        "scores": receipt["scores"],
        "atoms": [_atom(a) for a in receipt["atoms"]],
        "wire": [
            {
                "seq": w["seq"],
                "direction": w["direction"],
                "method": w["method"],
                "rpc_id": w["rpc_id"],
            }
            for w in receipt["wire"]
        ],
        "server_requests": receipt["server_requests"],
    }


def _atom(atom: dict[str, Any]) -> dict[str, Any]:
    session = atom.get("session") or {}
    return {
        "id": atom["id"],
        "result": atom["result"],
        "task": atom["task"],
        "poison_source": atom["poison_source"],
        "authorized_tools": atom["authorized_tools"],
        "checks": [{"id": c["id"], "result": c["result"]} for c in atom["checks"]],
        "calls": [
            {"name": c["name"], "arguments": c["arguments"], "is_error": c["is_error"]}
            for c in atom["calls"]
        ],
        "session": {
            "framing": session.get("framing"),
            "framing_source": session.get("framing_source"),
            "protocol_version": session.get("protocol_version"),
        },
    }


def dumps(receipt: dict[str, Any]) -> str:
    return json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def load(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def save(name: str, receipt: dict[str, Any]) -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    (FIXTURES / name).write_text(dumps(receipt), encoding="utf-8")
