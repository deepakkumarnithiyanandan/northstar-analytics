from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.agent import AgentProviderFailure, run_agent
from app.config import MAX_GOAL_LENGTH, OPENAI_API_KEY
from app import store

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    store.initialize()
    yield


app = FastAPI(title="Goal Planner Agent", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class GoalRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=MAX_GOAL_LENGTH)


class TaskCompletion(BaseModel):
    completed: bool


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "model_configured": bool(OPENAI_API_KEY)}


@app.get("/api/plans")
def plans():
    return store.list_plans()


@app.post("/api/agent/run")
async def create_goal_plan(payload: GoalRequest):
    goal = payload.goal.strip()
    if not goal:
        raise HTTPException(status_code=422, detail="Goal must contain 1 to 500 characters.")
    try:
        if OPENAI_API_KEY:
            async with httpx.AsyncClient(timeout=25) as client:
                return await run_agent(goal, client)
        return await run_agent(goal)
    except AgentProviderFailure as exc:
        raise HTTPException(status_code=502, detail="The planning agent failed. Check the provider settings and try again.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, payload: TaskCompletion):
    try:
        return store.set_task_completed(task_id, payload.completed)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task not found.") from exc
