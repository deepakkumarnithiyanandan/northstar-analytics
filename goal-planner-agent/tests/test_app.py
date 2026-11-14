import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app import agent, store
from app.main import app


def test_local_agent_saves_tasks_and_supports_progress(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATABASE_PATH", tmp_path / "plans.sqlite3")
    monkeypatch.setattr(agent, "OPENAI_API_KEY", "")

    with TestClient(app) as client:
        response = client.post("/api/agent/run", json={"goal": "Prepare for a job interview"})
        assert response.status_code == 200
        result = response.json()
        assert result["mode"] == "local"
        assert len(result["plan"]["tasks"]) == 5
        assert [step["tool"] for step in result["trace"]] == [
            "get_today_date",
            "estimate_total_minutes",
            "save_plan",
        ]

        task_id = result["plan"]["tasks"][0]["id"]
        updated = client.patch(f"/api/tasks/{task_id}", json={"completed": True})
        assert updated.status_code == 200
        assert updated.json()["completed"] == 1
        assert client.get("/api/plans").json()[0]["tasks"][0]["completed"] == 1


@pytest.mark.anyio
async def test_model_agent_uses_save_plan_tool(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATABASE_PATH", tmp_path / "plans.sqlite3")
    monkeypatch.setattr(agent, "OPENAI_API_KEY", "test-key")
    store.initialize()
    requests = []

    def handle(request):
        body = json.loads(request.content)
        requests.append(body)
        if body["tool_choice"] == "required":
            tool_calls = [{
                "id": "save_1",
                "type": "function",
                "function": {
                    "name": "save_plan",
                    "arguments": json.dumps({
                        "title": "Learn watercolor basics",
                        "tasks": [
                            {"title": "Gather paper and paints", "estimate_minutes": 20},
                            {"title": "Practice basic brush strokes", "estimate_minutes": 30},
                            {"title": "Paint a simple study", "estimate_minutes": 45},
                        ],
                    }),
                },
            }]
            return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "tool_calls": tool_calls}}]})
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": "I saved your starter plan."}}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle), base_url="http://model.test") as model:
        result = await agent.run_agent("Learn watercolor basics", model)

    assert result["mode"] == "agent"
    assert result["plan"]["title"] == "Learn watercolor basics"
    assert len(result["plan"]["tasks"]) == 3
    assert result["trace"][0]["tool"] == "save_plan"
    assert requests[0]["tool_choice"] == "required"


def test_goal_and_task_validation(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATABASE_PATH", tmp_path / "plans.sqlite3")
    store.initialize()
    with TestClient(app) as client:
        assert client.post("/api/agent/run", json={"goal": " "}).status_code == 422
        assert client.patch("/api/tasks/999", json={"completed": True}).status_code == 404


def test_workspace_is_served(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATABASE_PATH", tmp_path / "plans.sqlite3")
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "Daymark" in response.text
