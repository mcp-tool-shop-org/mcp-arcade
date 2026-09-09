from click.testing import CliRunner

from mcp_arcade.cli import app


def test_version() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "1.0.0" in result.output


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
