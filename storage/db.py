# agent/storage/db.py

import sqlite3
import os
import mysql.connector
from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from auth.session import get_current_user

DB_PATH = os.path.join(os.path.dirname(__file__), "local.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def get_mysql_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )


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


def get_open_session_activity(username):
    """
    Fetch the most recent open login session for the user
    from MySQL activity table (logout_time is NULL).
    """
    conn = None
    cursor = None
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, username, action, login_time, logout_time, idle_time
            FROM activity
            WHERE LOWER(TRIM(username)) = LOWER(TRIM(%s))
              AND action = 'login'
              AND logout_time IS NULL
            ORDER BY id DESC
            LIMIT 1
        """, (username,))

        row = cursor.fetchone()
        return row  # Returns dict or None

    except Exception as e:
        print(f"❌ [SESSION] Error fetching open session: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_user_tasks():
    """Fetch tasks for the currently logged-in user from MySQL."""
    conn = None
    cursor = None
    try:
        session = get_current_user()

        if not session:
            print("❌ [TASKS] No active session found")
            return []

        username = (session.get("username") or "").strip()
        email = (session.get("email") or "").strip()

        print(f"🔍 [TASKS] Session user object: {session}")
        print(f"🔍 [TASKS] Resolved username for query: '{username}'")

        if not username and not email:
            print("❌ [TASKS] No username or email in session")
            return []

        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                id, userId, title, description, status,
                createdAt, deadline, priority,
                assignedBy, assignedTo, email, domain
            FROM tasks
            WHERE LOWER(TRIM(userId)) = LOWER(TRIM(%s))
               OR LOWER(TRIM(assignedTo)) = LOWER(TRIM(%s))
               OR LOWER(TRIM(email)) = LOWER(TRIM(%s))
            ORDER BY id DESC
        """, (username, username, email))

        tasks = cursor.fetchall()

        for task in tasks:
            if task.get("createdAt") and not isinstance(task["createdAt"], str):
                task["createdAt"] = task["createdAt"].isoformat()
            if task.get("deadline"):
                task["deadline"] = str(task["deadline"])

        print(f"✅ [TASKS] Found {len(tasks)} task(s) for '{username}'")
        return tasks

    except Exception as e:
        print(f"❌ [TASKS] DB Error: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def update_task_status(task_id, status):
    """Update task status in MySQL."""
    conn = None
    cursor = None
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE tasks SET status = %s WHERE id = %s",
            (status, task_id)
        )

        if cursor.rowcount == 0:
            print(f"⚠️ [TASKS] Task {task_id} not found")
            return False

        conn.commit()
        print(f"✅ [TASKS] Task {task_id} marked as '{status}'")
        return True

    except Exception as e:
        print(f"❌ [TASKS] Update Error: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==========================================
# LOGGING FUNCTIONS
# ==========================================

def log_login(*args, **kwargs):
    """Log user login to the database."""
    # Returning dummy IDs for _activity_id, _logs_id
    return 1, 1

def log_logout(*args, **kwargs):
    """Log user logout to the database."""
    pass

def log_activity(*args, **kwargs):
    """Log an activity to the database."""
    pass

def log_idle_time(*args, **kwargs):
    """Log idle time to the database."""
    pass