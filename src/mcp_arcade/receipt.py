"""Canonical bout receipts. Dataset-shaped on purpose.

Later optional Ollama seats train or judge from `calls` + `observations`.
They do not get `operator_call` as a label. Split is recorded so a holdout
atom can exist without leaking into a leaderboard.
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp_arcade.models import BoutReceipt


def canonical_dumps(receipt: BoutReceipt) -> str:
    payload = receipt.model_dump(mode="json")
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_receipt(path: Path, receipt: BoutReceipt) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_dumps(receipt), encoding="utf-8")


def read_receipt(path: Path) -> BoutReceipt:
    data = json.loads(path.read_text(encoding="utf-8"))
    return BoutReceipt.model_validate(data)
