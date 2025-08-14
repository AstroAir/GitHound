import pytest
from git import Repo
from pathlib import Path
from githound.git_handler import get_repository, walk_history, process_commit
from githound.models import GitHoundConfig, SearchConfig

@pytest.fixture
def temp_repo(tmp_path):
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    repo = Repo.init(repo_path)
    (repo_path / "file1.txt").write_text("hello world")
    repo.index.add(["file1.txt"])
    repo.index.commit("initial commit")
    return repo_path

def test_get_repository(temp_repo):
    repo = get_repository(temp_repo)
    assert repo is not None
    assert isinstance(repo, Repo)

def test_walk_history(temp_repo):
    config = GitHoundConfig(
        repo_path=temp_repo,
        search_query="hello",
    )
    repo = get_repository(temp_repo)
    commits = list(walk_history(repo, config))
    assert len(commits) == 1

def test_process_commit(temp_repo):
    config = GitHoundConfig(
        repo_path=temp_repo,
        search_query="hello",
    )
    repo = get_repository(temp_repo)
    commit = repo.head.commit
    results = process_commit(commit, config)
    assert len(results) == 1
    assert results[0].matching_line == "hello world"