# Goal Planner Agent

A small, standalone agent that turns a goal into a saved, actionable task plan. The optional model agent can use a bounded set of tools to check today's date, total estimates, and save tasks to a local SQLite database. Its UI shows the tool trace and lets you mark tasks complete.

The app is independent of other workspace projects and needs no external data. Without an API key it uses a deterministic local planner; with a key it uses the configured OpenAI-compatible chat-completions API.

## Run locally

```powershell
cd goal-planner-agent
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `OPENAI_API_KEY` in `.env` to enable model-driven planning. Then start the app:

```powershell
uvicorn app.main:app --reload --port 8002
```

Open `http://localhost:8002`. Plans are stored locally at `data\plans.sqlite3`. Run tests with `python -m pytest -q`.

## Agent tools

- `get_today_date`: returns the current local date.
- `estimate_total_minutes`: sums bounded task time estimates.
- `save_plan`: saves the goal and its 3–8 actionable tasks to the local task list.

The agent can execute at most four tool calls per request. It cannot run commands, access arbitrary files, browse the web, or call tools outside this list. The local fallback follows the same save-plan flow without a model provider.

## Configuration

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Optional model-provider key; blank uses the local planner. |
| `OPENAI_BASE_URL` | Chat-completions API root; defaults to `https://api.openai.com/v1`. |
| `OPENAI_MODEL` | Model name; defaults to `gpt-4o-mini`. |
| `GOAL_PLANNER_DB` | Optional path for the local SQLite database. |

With a model key configured, the user's goal and generated task plan are sent to that provider. Avoid entering sensitive information unless the provider is approved for it.
