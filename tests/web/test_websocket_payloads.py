import json
from typing import Any

import pytest

from githound.web.websocket import (
    ConnectionManager,
    ProgressMessage,
)


@pytest.mark.asyncio
async def test_broadcast_progress_builds_typed_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    cm = ConnectionManager()

    captured: dict[str, Any] = {}

    async def fake_broadcast(search_id: str, message: dict[str, Any]) -> None:
        captured["search_id"] = search_id
        captured["message"] = message

    monkeypatch.setattr(cm, "broadcast_to_search", fake_broadcast)

    await cm.broadcast_progress("sid", 0.5, "processing", results_count=3)

    assert captured["search_id"] == "sid"
    msg = captured["message"]
    assert isinstance(msg, dict)
    assert msg["type"] == "progress"
    data = msg["data"]
    assert data["search_id"] == "sid"
    assert data["progress"] == pytest.approx(0.5)
    assert data["message"] == "processing"
    assert data["results_count"] == 3
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_broadcast_result_builds_typed_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    cm = ConnectionManager()

    captured: dict[str, Any] = {}

    async def fake_broadcast(search_id: str, message: dict[str, Any]) -> None:
        captured["search_id"] = search_id
        captured["message"] = message

    monkeypatch.setattr(cm, "broadcast_to_search", fake_broadcast)

    result_obj = {"id": 1, "value": "hit"}
    await cm.broadcast_result("sid", result_obj)

    assert captured["search_id"] == "sid"
    msg = captured["message"]
    assert msg["type"] == "result"
    data = msg["data"]
    assert data["search_id"] == "sid"
    assert data["result"] == result_obj
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_broadcast_completion_builds_typed_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    cm = ConnectionManager()

    captured: dict[str, Any] = {}

    async def fake_broadcast(search_id: str, message: dict[str, Any]) -> None:
        captured["search_id"] = search_id
        captured["message"] = message

    monkeypatch.setattr(cm, "broadcast_to_search", fake_broadcast)

    await cm.broadcast_completion("sid", "completed", total_results=7, error_message=None)

    assert captured["search_id"] == "sid"
    msg = captured["message"]
    assert msg["type"] == "completed"
    data = msg["data"]
    assert data["search_id"] == "sid"
    assert data["status"] == "completed"
    assert data["total_results"] == 7
    assert data["error_message"] is None
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_broadcast_error_builds_typed_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    cm = ConnectionManager()

    captured: dict[str, Any] = {}

    async def fake_broadcast(search_id: str, message: dict[str, Any]) -> None:
        captured["search_id"] = search_id
        captured["message"] = message

    monkeypatch.setattr(cm, "broadcast_to_search", fake_broadcast)

    await cm.broadcast_error("sid", "oops")

    assert captured["search_id"] == "sid"
    msg = captured["message"]
    assert msg["type"] == "error"
    data = msg["data"]
    assert data["search_id"] == "sid"
    assert data["error"] == "oops"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_send_personal_message_json_serializes(monkeypatch: pytest.MonkeyPatch) -> None:
    cm = ConnectionManager()

    sent: dict[str, Any] = {}

    class DummyWS:
        async def send_text(self, s: str) -> None:
            sent["text"] = s

    ws = DummyWS()
    payload: ProgressMessage = {
        "type": "progress",
        "data": {
            "search_id": "sid",
            "progress": 0.1,
            "message": "boot",
            "results_count": 0,
            "timestamp": "2020-01-01T00:00:00Z",
        },
    }

    await cm.send_personal_message(ws, payload)  # [arg-type]

    assert "text" in sent
    # Should be valid JSON with correct top-level keys
    parsed = json.loads(sent["text"])  # may raise if invalid
    assert parsed["type"] == "progress"
    assert parsed["data"]["search_id"] == "sid"
