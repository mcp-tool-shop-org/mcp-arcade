"""CLI surface. `--cmd` quoting on Windows is a wave-1 deliverable."""

from __future__ import annotations

import json
import sys

import pytest
from click.testing import CliRunner

from mcp_arcade.cli import app, split_command


def test_version() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_atoms_lists_three() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["atoms"])
    assert result.exit_code == 0
    assert "inspect.tools_list" in result.output
    assert "poison.follow_through" in result.output
    assert "temporal.rug_pull" in result.output


def test_bout_requires_target() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["bout"])
    assert result.exit_code != 0


def test_bout_fixture_task_only(tmp_path) -> None:
    runner = CliRunner()
    out = tmp_path / "receipt.json"
    sandbox = tmp_path / "box"
    result = runner.invoke(
        app,
        [
            "bout",
            "--target",
            "fixture",
            "--agent",
            "task-only",
            "--no-prompt",
            "-o",
            str(out),
            "--sandbox",
            str(sandbox),
        ],
    )
    assert result.exit_code == 0, result.output
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "mcp-arcade.bout/v1" in text
    assert "operator_call" in text
    assert "The Honest Menu" in result.output
    assert "House call" in result.output


# ----- wave 1: --cmd quoting, the named task, framing and timeout -----


def test_split_command_splits_one_quoted_string() -> None:
    assert split_command(("npx -y my-server",)) == ["npx", "-y", "my-server"]


def test_split_command_leaves_the_repeatable_form_alone() -> None:
    assert split_command(("python", "-m", "x")) == ["python", "-m", "x"]
    assert split_command(("my-server",)) == ["my-server"]


@pytest.mark.skipif(sys.platform != "win32", reason="non-POSIX shlex rules are a Windows thing")
def test_split_command_keeps_windows_backslashes() -> None:
    argv = split_command((r"D:\tools\venv\Scripts\python.exe -m my_server",))
    assert argv == [r"D:\tools\venv\Scripts\python.exe", "-m", "my_server"]


@pytest.mark.skipif(sys.platform != "win32", reason="non-POSIX shlex rules are a Windows thing")
def test_split_command_strips_inner_quotes_around_a_path_with_spaces() -> None:
    argv = split_command((r'"C:\Program Files\py\python.exe" -m my_server',))
    assert argv[0] == r"C:\Program Files\py\python.exe"


def test_bout_help_lists_the_wave_1_options() -> None:
    result = CliRunner().invoke(app, ["bout", "--help"])
    assert result.exit_code == 0
    for option in ("--task", "--args", "--wrap", "--framing", "--timeout"):
        assert option in result.output


def test_bout_with_an_operator_named_task(tmp_path) -> None:
    out = tmp_path / "receipt.json"
    result = CliRunner().invoke(
        app,
        [
            "bout",
            "--target",
            "fixture",
            "--agent",
            "task-only",
            "--no-prompt",
            "--task",
            "echo",
            "--args",
            '{"text":"hi"}',
            "-o",
            str(out),
            "--sandbox",
            str(tmp_path / "box"),
        ],
    )
    assert result.exit_code == 0, result.output
    receipt = json.loads(out.read_text(encoding="utf-8"))
    assert receipt["task"] == {"tool": "echo", "arguments": {"text": "hi"}, "source": "operator"}
    assert all(a["task"]["source"] == "operator" for a in receipt["atoms"])
    assert "operator" in out.read_text(encoding="utf-8")


def test_args_without_task_is_refused(tmp_path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "bout",
            "--target",
            "fixture",
            "--no-prompt",
            "--args",
            '{"text":"hi"}',
            "--sandbox",
            str(tmp_path / "box"),
        ],
    )
    assert result.exit_code != 0
    assert "--args needs --task" in result.output


def test_args_must_be_json(tmp_path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "bout",
            "--target",
            "fixture",
            "--no-prompt",
            "--task",
            "echo",
            "--args",
            "notjson",
            "--sandbox",
            str(tmp_path / "box"),
        ],
    )
    assert result.exit_code != 0
    assert "not valid JSON" in result.output


def test_args_must_be_a_json_object(tmp_path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "bout",
            "--target",
            "fixture",
            "--no-prompt",
            "--task",
            "echo",
            "--args",
            "[1,2]",
            "--sandbox",
            str(tmp_path / "box"),
        ],
    )
    assert result.exit_code != 0
    assert "must be a JSON object" in result.output


def test_bout_with_content_length_framing(tmp_path) -> None:
    out = tmp_path / "receipt.json"
    result = CliRunner().invoke(
        app,
        [
            "bout",
            "--target",
            "fixture",
            "--agent",
            "task-only",
            "--no-prompt",
            "--framing",
            "content-length",
            "-o",
            str(out),
            "--sandbox",
            str(tmp_path / "box"),
        ],
    )
    assert result.exit_code == 0, result.output
    receipt = json.loads(out.read_text(encoding="utf-8"))
    assert receipt["target"]["framing"] == "content-length"
    assert all(a["session"]["framing"] == "content-length" for a in receipt["atoms"])


def test_bout_accepts_a_timeout(tmp_path) -> None:
    out = tmp_path / "receipt.json"
    result = CliRunner().invoke(
        app,
        [
            "bout",
            "--target",
            "fixture",
            "--agent",
            "task-only",
            "--no-prompt",
            "--timeout",
            "0.5",
            "-o",
            str(out),
            "--sandbox",
            str(tmp_path / "box"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(out.read_text(encoding="utf-8"))["target"]["timeout_s"] == 0.5


def test_bout_rejects_a_non_numeric_timeout(tmp_path) -> None:
    result = CliRunner().invoke(
        app, ["bout", "--target", "fixture", "--no-prompt", "--timeout", "soon"]
    )
    assert result.exit_code != 0
    assert "not a valid float" in result.output.lower()


def test_stdio_target_needs_allow_live(tmp_path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "bout",
            "--target",
            "stdio",
            "--cmd",
            "python -m mcp_arcade.fixture",
            "--no-prompt",
            "--sandbox",
            str(tmp_path / "box"),
        ],
    )
    assert result.exit_code != 0
    assert "allow-live" in result.output
