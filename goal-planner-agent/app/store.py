import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

from app.config import DATABASE_PATH


@contextmanager
def _connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize() -> None:
    with _connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
                position INTEGER NOT NULL,
                title TEXT NOT NULL,
                estimate_minutes INTEGER NOT NULL CHECK (estimate_minutes BETWEEN 5 AND 600),
                completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1))
            );
            """
        )


def create_plan(goal: str, title: str, tasks: list[dict[str, Any]]) -> dict[str, Any]:
    if not 3 <= len(tasks) <= 8:
        raise ValueError("A plan must contain between 3 and 8 tasks.")
    if not isinstance(title, str) or not title.strip() or len(title) > 120:
        raise ValueError("Plan title must contain 1 to 120 characters.")
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("Each task must be an object.")
        task_title = task.get("title")
        minutes = task.get("estimate_minutes")
        if not isinstance(task_title, str) or not task_title.strip() or len(task_title) > 160:
            raise ValueError("Each task needs a title of 1 to 160 characters.")
        if not isinstance(minutes, int) or isinstance(minutes, bool) or not 5 <= minutes <= 600:
            raise ValueError("Each task estimate must be between 5 and 600 minutes.")
    created_at = datetime.now(timezone.utc).isoformat()
    with _connection() as connection:
        cursor = connection.execute(
            "INSERT INTO plans (goal, title, created_at) VALUES (?, ?, ?)",
            (goal, title.strip(), created_at),
        )
        plan_id = cursor.lastrowid
        connection.executemany(
            "INSERT INTO tasks (plan_id, position, title, estimate_minutes) VALUES (?, ?, ?, ?)",
            [(plan_id, index, task["title"].strip(), task["estimate_minutes"]) for index, task in enumerate(tasks)],
        )
    return get_plan(plan_id)


def get_plan(plan_id: int) -> dict[str, Any]:
    with _connection() as connection:
        plan = connection.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
        if plan is None:
            raise KeyError("Plan not found.")
        tasks = connection.execute(
            "SELECT id, title, estimate_minutes, completed FROM tasks WHERE plan_id = ? ORDER BY position",
            (plan_id,),
        ).fetchall()
    return {
        "id": plan["id"],
        "goal": plan["goal"],
        "title": plan["title"],
        "created_at": plan["created_at"],
        "tasks": [dict(task) for task in tasks],
    }


def list_plans() -> list[dict[str, Any]]:
    with _connection() as connection:
        plan_ids = connection.execute("SELECT id FROM plans ORDER BY id DESC").fetchall()
    return [get_plan(row["id"]) for row in plan_ids]


def set_task_completed(task_id: int, completed: bool) -> dict[str, Any]:
    with _connection() as connection:
        cursor = connection.execute("UPDATE tasks SET completed = ? WHERE id = ?", (int(completed), task_id))
        if cursor.rowcount == 0:
            raise KeyError("Task not found.")
        row = connection.execute(
            "SELECT id, title, estimate_minutes, completed FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
    return dict(row)
