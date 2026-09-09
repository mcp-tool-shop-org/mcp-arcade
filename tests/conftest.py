"""Shared pytest configuration.

The `docker` marker is registered here rather than in pyproject so the
marker travels with the tests that use it. Live docker tests also carry a
`skipif` on the daemon, so an unmarked run on a machine without Docker
still goes green; the marker exists so CI can say `-m "not docker"`.
"""

from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "docker: needs a reachable Docker daemon (wave 2 — Docker is the sandbox)",
    )
