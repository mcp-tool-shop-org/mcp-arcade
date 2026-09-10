"""Committed proof receipts are public. They must not carry a host home path,
in any JSON escaping (the identity scanner misses double-escaped backslashes)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PROOFS = sorted(Path("docs/proof").glob("*.json"))
HOME_PATH = re.compile(r"(?i)[a-z]:\\{1,4}users\\{1,4}|/users/|/home/[a-z]")


@pytest.mark.parametrize("path", PROOFS, ids=[p.name for p in PROOFS])
def test_proof_receipt_has_no_host_home_path(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    hit = HOME_PATH.search(text)
    assert hit is None, (
        f"{path.name}: host home path on the receipt at {hit.start()}: {hit.group(0)!r}"
    )


def test_proofs_exist() -> None:
    assert PROOFS, "docs/proof should hold the committed live receipts"
