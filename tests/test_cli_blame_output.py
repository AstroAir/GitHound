import tempfile
from pathlib import Path

from git import Repo
from typer.testing import CliRunner

from githound.cli import app


def _init_temp_repo(tmp_dir: Path) -> tuple[Repo, Path, str]:
    repo = Repo.init(tmp_dir)
    with repo.config_writer() as cw:  # [attr-defined]
        cw.set_value("user", "name", "Test User")  # [attr-defined]
        cw.set_value("user", "email", "test@example.com")  # [attr-defined]

    file_path = tmp_dir / "sample.txt"
    file_path.write_text("line one\nline two\n")
    repo.index.add(["sample.txt"])
    repo.index.commit("initial")

    # Make a small change to have richer blame data
    file_path.write_text("line one\nline two updated\n")
    repo.index.add(["sample.txt"])
    repo.index.commit("update second line")

    return repo, file_path, "sample.txt"


def test_cli_blame_text_output_succeeds(tmp_path: Path) -> None:
    # Arrange: create a small git repo with a file
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _repo, file_path, rel_path = _init_temp_repo(repo_dir)

    # Act: run the CLI blame command in TEXT mode (default)
    runner = CliRunner()
    result = runner.invoke(app, ["blame", str(repo_dir), rel_path])

    # Assert: exit code is success and output contains header
    assert result.exit_code == 0, f"CLI stderr/stdout:\n{result.stdout}"
    assert "File Blame Analysis" in result.stdout
    assert "File:" in result.stdout