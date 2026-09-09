"""Sandbox file snapshots. The env oracle, not the TUI."""

from __future__ import annotations

from pathlib import Path

from mcp_arcade.models import EnvSnapshot


def snapshot_dir(path: Path | None) -> EnvSnapshot:
    if path is None or not path.exists():
        return EnvSnapshot()
    files: dict[str, str] = {}
    if path.is_file():
        files[path.name] = path.read_text(encoding="utf-8", errors="replace")
        return EnvSnapshot(files=files)
    for child in sorted(path.iterdir()):
        if child.is_file():
            files[child.name] = child.read_text(encoding="utf-8", errors="replace")
    return EnvSnapshot(files=files)
