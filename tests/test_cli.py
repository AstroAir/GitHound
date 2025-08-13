import pytest
from typer.testing import CliRunner

import githound.cli
from githound.cli import app

runner = CliRunner()


def test_cli_no_args():
    result = runner.invoke(app, [])
    assert result.exit_code != 0
    assert "Missing option" in result.stdout


def test_cli_with_query_and_repo(mocker):
    mock_search = mocker.patch('githound.cli.search_and_print')
    result = runner.invoke(app, ['--repo-path', '.', '--search-query', 'test_query'])
    assert result.exit_code == 0
    mock_search.assert_called_once()


def test_cli_with_branch(mocker):
    mock_search = mocker.patch('githound.cli.search_and_print')
    result = runner.invoke(app, ['--repo-path', '.', '--search-query', 'test_query', '--branch', 'develop'])
    assert result.exit_code == 0
    mock_search.assert_called_once()


def test_cli_with_json_output(mocker):
    mock_search = mocker.patch('githound.cli.search_and_print')
    result = runner.invoke(app, ['--repo-path', '.', '--search-query', 'test_query', '--output-format', 'json'])
    assert result.exit_code == 0
    mock_search.assert_called_once()