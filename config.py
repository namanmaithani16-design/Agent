# agent/config.py

import os
from pathlib import Path


def _load_env_file():
    """Load simple KEY=VALUE pairs from .env without requiring extra packages."""
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file()


API_BASE_URL = os.getenv("API_BASE_URL", "http://[IP_ADDRESS]/api")

SCREENSHOT_INTERVAL = int(os.getenv("SCREENSHOT_INTERVAL", "3600"))   # 1 hour
IDLE_LIMIT = int(os.getenv("IDLE_LIMIT", "600"))                      # 10 minutes

APP_NAME = os.getenv("APP_NAME", "ISMS Agent")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "isms")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
