from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from githound.web.api import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def temp_repo(tmp_path: Path):
    # Create a temporary git repo structure; tests rely only on path existence
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    # Create a .git folder to pass simple checks where needed
    (repo_dir / ".git").mkdir(exist_ok=True)
    yield str(repo_dir)


def test_search_lifecycle_and_list_searches(client: TestClient, temp_repo: str) -> None:
    # Start a search
    start_resp = client.post(
        "/api/search",
        json={
            "repo_path": temp_repo,
            "query": "hello",
            "branch": None,
            "max_results": 10,
        },
    )
    assert start_resp.status_code == 200
    sid = start_resp.json()["search_id"]

    # Status should be present
    status_resp = client.get(f"/api/search/{sid}/status")
    assert status_resp.status_code == 200
    status = status_resp.json()
    assert status["search_id"] == sid
    assert status["status"] in {"starting", "running", "completed", "error"}

    # Poll results (might be 202 if not ready yet)
    results_resp = client.get(f"/api/search/{sid}/results")
    assert results_resp.status_code in {200, 202, 500}

    # List searches includes this id
    list_resp = client.get("/api/searches")
    assert list_resp.status_code == 200
    list_payload = list_resp.json()
    assert "searches" in list_payload
    assert any(item["search_id"] == sid for item in list_payload["searches"])
