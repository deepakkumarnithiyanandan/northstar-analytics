import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DATABASE_PATH = Path(os.getenv("GOAL_PLANNER_DB", str(PROJECT_DIR / "data" / "plans.sqlite3")))
MAX_TOOL_CALLS = 4
MAX_GOAL_LENGTH = 500
