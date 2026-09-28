import os


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./analytics.db")
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
MAX_UPLOAD_ROWS = int(os.getenv("MAX_UPLOAD_ROWS", "100000"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")