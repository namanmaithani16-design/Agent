# agent/storage/db.py

import sqlite3
import os

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "local.db"
)

def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            app_name TEXT,
            start_time TEXT,
            end_time TEXT,
            duration INTEGER
        )
    """)

    conn.commit()
    conn.close()
