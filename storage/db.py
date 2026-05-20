# agent/storage/db.py

import sqlite3
import os
import mysql.connector
from datetime import datetime, timezone, timedelta
from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from auth.session import get_current_user

IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    """Return current datetime in IST (UTC+5:30)."""
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")

DB_PATH = os.path.join(os.path.dirname(__file__), "local.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def get_mysql_connection():
    print(f"[DB] Connecting -> host={DB_HOST}, user={DB_USER}, "
          f"db={DB_NAME}, port={DB_PORT}, "
          f"password={'SET' if DB_PASSWORD else 'EMPTY/MISSING'}")

    if not DB_PASSWORD:
        raise ValueError(
            "DB_PASSWORD is empty or None. "
            "Set it in your config.py or .env file."
        )

    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )


def _column_names(cursor, table_name):
    cursor.execute(f"SHOW COLUMNS FROM {table_name}")
    columns = set()
    for row in cursor.fetchall():
        if isinstance(row, dict):
            columns.add(row.get("Field"))
        else:
            columns.add(row[0])
    return columns


def ensure_mysql_activity_table(cursor):
    expected_columns = {
        "email": "ALTER TABLE activity ADD COLUMN email VARCHAR(150)",
        "domain": "ALTER TABLE activity ADD COLUMN domain VARCHAR(150)",
        "designation": "ALTER TABLE activity ADD COLUMN designation VARCHAR(150)",
        "role": "ALTER TABLE activity ADD COLUMN role VARCHAR(50)",
        "metadata": "ALTER TABLE activity ADD COLUMN metadata TEXT",
        "created_at": "ALTER TABLE activity ADD COLUMN created_at DATETIME",
    }

    existing_columns = _column_names(cursor, "activity")
    for column_name, alter_sql in expected_columns.items():
        if column_name not in existing_columns:
            cursor.execute(alter_sql)


def update_account_status(cursor, username=None, email=None, status="offline", last_seen=None):
    username = (username or "").strip()
    email = (email or "").strip()

    if not username and not email:
        return

    normalized_status = "online" if str(status).lower() == "online" else "offline"

    for table_name in ("users", "admins"):
        cursor.execute(
            f"""
            UPDATE {table_name}
            SET status = %s,
                last_seen = %s
            WHERE (%s <> '' AND LOWER(TRIM(username)) = LOWER(TRIM(%s)))
               OR (%s <> '' AND LOWER(TRIM(email)) = LOWER(TRIM(%s)))
            """,
            (
                normalized_status,
                last_seen,
                username,
                username,
                email,
                email,
            ),
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
    conn = None
    cursor = None
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, username, action, login_time, logout_time, idle_time
            FROM activity
            WHERE LOWER(TRIM(username)) = LOWER(TRIM(%s))
              AND action = 'session'
              AND logout_time IS NULL
            ORDER BY id DESC
            LIMIT 1
        """, (username,))

        row = cursor.fetchone()
        return row

    except Exception as e:
        print(f"[SESSION] Error fetching open session: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_user_tasks():
    conn = None
    cursor = None
    try:
        session = get_current_user()

        if not session:
            print("[TASKS] No active session found")
            return []

        username = (session.get("username") or "").strip()
        email = (session.get("email") or "").strip()

        if not username and not email:
            print("[TASKS] No username or email in session")
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

        print(f"[TASKS] Found {len(tasks)} task(s) for '{username}'")
        return tasks

    except Exception as e:
        print(f"[TASKS] DB Error: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def update_task_status(task_id, status):
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
            print(f"[TASKS] Task {task_id} not found")
            return False

        conn.commit()
        print(f"[TASKS] Task {task_id} marked as '{status}'")
        return True

    except Exception as e:
        print(f"[TASKS] Update Error: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==========================================
# LOGGING FUNCTIONS
# ==========================================

def resolve_account(cursor, username=None, email=None):
    username = (username or "").strip()
    email = (email or "").strip()

    for table_name in ("users", "admins"):
        cursor.execute(
            f"""
            SELECT id, username, email, domain, role, designation
            FROM {table_name}
            WHERE (%s <> '' AND LOWER(TRIM(username)) = LOWER(TRIM(%s)))
               OR (%s <> '' AND LOWER(TRIM(email)) = LOWER(TRIM(%s)))
            LIMIT 1
            """,
            (username, username, email, email),
        )
        account = cursor.fetchone()
        if account:
            return account

    return None


def mark_closed_logs_as_logout(cursor, username=None, email=None):
    username = (username or "").strip()
    email = (email or "").strip()

    if not username and not email:
        return

    cursor.execute(
        """
        UPDATE logs
        SET action = 'logout'
        WHERE logout_time IS NOT NULL
          AND COALESCE(action, '') <> 'logout'
          AND (
            (%s <> '' AND LOWER(TRIM(username)) = LOWER(TRIM(%s)))
            OR (%s <> '' AND LOWER(TRIM(email)) = LOWER(TRIM(%s)))
          )
        """,
        (username, username, email, email),
    )


def log_login():
    conn = None
    cursor = None
    activity_id = None
    logs_id = None

    try:
        session = get_current_user()
        if not session:
            print("[LOG_LOGIN] No active session found")
            return None, None

        user_id = session.get("user_id")
        username = session.get("username")
        email = session.get("email")
        role = session.get("role")
        domain = session.get("domain")
        designation = session.get("designation")

        now = now_ist()

        conn   = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        ensure_mysql_activity_table(cursor)

        account = resolve_account(cursor, username=username, email=email)
        if account:
            user_id = user_id or account.get("id")
            username = username or account.get("username")
            email = email or account.get("email")
            domain = domain or account.get("domain")
            role = role or account.get("role")
            designation = designation or account.get("designation")

        update_account_status(cursor, username=username, email=email, status="online", last_seen=now)
        mark_closed_logs_as_logout(cursor, username=username, email=email)

        cursor.execute("""
            UPDATE logs
            SET logout_time = %s,
                action = 'logout'
            WHERE LOWER(TRIM(username)) = LOWER(TRIM(%s))
              AND logout_time IS NULL
        """, (now, username))

        cursor.execute("""
            UPDATE activity
            SET logout_time = %s
            WHERE LOWER(TRIM(username)) = LOWER(TRIM(%s))
              AND action = 'session'
              AND logout_time IS NULL
        """, (now, username))

        cursor.execute("""
            INSERT INTO logs (user_id, username, email, domain, login_time, role, designation, action, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, username, email, domain, now, role, designation, "login", now))
        logs_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO activity
                (username, email, domain, designation, role, app_name, action, login_time, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (username, email, domain, designation, role, "system", "session", now, now))
        activity_id = cursor.lastrowid

        conn.commit()
        print(f"[LOG_LOGIN] Logged login - logs_id={logs_id}, activity_id={activity_id}")

    except Exception as e:
        print(f"[LOG_LOGIN] Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return activity_id, logs_id


def log_logout(activity_id=None, logs_id=None):
    conn = None
    cursor = None

    print(f"[LOG_LOGOUT] Called with activity_id={activity_id}, logs_id={logs_id}")

    if activity_id is None and logs_id is None and not get_current_user():
        print("[LOG_LOGOUT] Both IDs are None - nothing to update")
        return

    try:
        session = get_current_user()
        username = session.get("username") if session else None
        email = session.get("email") if session else None
        now = now_ist()
        print(f"[LOG_LOGOUT] Logout time (IST): {now}")

        conn = get_mysql_connection()
        cursor = conn.cursor()

        if username or email:
            update_account_status(cursor, username=username, email=email, status="offline", last_seen=now)

        if logs_id is not None:
            print(f"[LOG_LOGOUT] Updating logs table for id={logs_id}")
            cursor.execute("""
                UPDATE logs
                SET logout_time = %s,
                    action = 'logout'
                WHERE id = %s
            """, (now, logs_id))
            print(f"[LOG_LOGOUT] logs rowcount={cursor.rowcount} for id={logs_id}")

        if activity_id is not None:
            print(f"[LOG_LOGOUT] Updating activity table for id={activity_id}")
            cursor.execute("""
                UPDATE activity SET logout_time = %s
                WHERE id = %s
            """, (now, activity_id))
            print(f"[LOG_LOGOUT] activity rowcount={cursor.rowcount} for id={activity_id}")

        if username or email:
            print(f"[LOG_LOGOUT] Closing latest open session for username='{username}', email='{email}'")

            cursor.execute("""
                UPDATE logs
                SET logout_time = %s,
                    action = 'logout'
                WHERE logout_time IS NULL
                  AND (
                    LOWER(TRIM(username)) = LOWER(TRIM(%s))
                    OR LOWER(TRIM(email)) = LOWER(TRIM(%s))
                  )
                ORDER BY id DESC
                LIMIT 1
            """, (now, username or "", email or ""))
            print(f"[LOG_LOGOUT] latest logs rowcount={cursor.rowcount}")

            mark_closed_logs_as_logout(cursor, username=username, email=email)

            cursor.execute("""
                UPDATE activity
                SET logout_time = %s
                WHERE action = 'session'
                  AND logout_time IS NULL
                  AND (
                    LOWER(TRIM(username)) = LOWER(TRIM(%s))
                    OR LOWER(TRIM(email)) = LOWER(TRIM(%s))
                  )
                ORDER BY id DESC
                LIMIT 1
            """, (now, username or "", email or ""))
            print(f"[LOG_LOGOUT] latest activity rowcount={cursor.rowcount}")

        conn.commit()
        print("[LOG_LOGOUT] Commit successful")

    except Exception as e:
        print(f"[LOG_LOGOUT] Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("[LOG_LOGOUT] Connection closed")


def log_activity(action, app_name=None, start_time=None, end_time=None, duration=None,
                 idle_time=None, screenshot_path=None, app_url=None, metadata=None):
    conn = None
    cursor = None

    try:
        session = get_current_user()
        username = session.get("username") if session else None
        email = session.get("email") if session else None
        domain = session.get("domain") if session else None
        role = session.get("role") if session else None
        designation = session.get("designation") if session else None
        created_at = now_ist()

        conn   = get_mysql_connection()
        cursor = conn.cursor()
        ensure_mysql_activity_table(cursor)

        if action in {"heartbeat", "screenshot", "app_usage"}:
            update_account_status(
                cursor,
                username=username,
                email=email,
                status="online",
                last_seen=created_at,
            )

        cursor.execute("""
            INSERT INTO activity
                (username, email, domain, designation, role, app_name, start_time, end_time, duration,
                 action, idle_time, screenshot_path, app_url, metadata, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            username, email, domain, designation, role, app_name, start_time, end_time, duration,
            action, idle_time, screenshot_path, app_url, metadata, created_at
        ))

        conn.commit()
        print(f"[LOG_ACTIVITY] Logged action='{action}' for '{username}'")

    except Exception as e:
        print(f"[LOG_ACTIVITY] Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def log_idle_time(idle_seconds):
    conn = None
    cursor = None

    try:
        session = get_current_user()
        if not session:
            return

        username = session.get("username")

        conn   = get_mysql_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE activity
            SET idle_time = %s
            WHERE LOWER(TRIM(username)) = LOWER(TRIM(%s))
              AND logout_time IS NULL
            ORDER BY id DESC
            LIMIT 1
        """, (idle_seconds, username))

        conn.commit()
        print(f"[LOG_IDLE] Updated idle_time={idle_seconds}s for '{username}'")

    except Exception as e:
        print(f"[LOG_IDLE] Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
