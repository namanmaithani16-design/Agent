from flask import Blueprint, request, jsonify
import mysql.connector
import os
from datetime import datetime, timedelta
from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

activity_bp = Blueprint("activity_bp", __name__)
ACTIVE_SESSION_TIMEOUT_SECONDS = int(os.getenv("ACTIVE_SESSION_TIMEOUT_SECONDS", "180"))


def normalize_domain(domain):
    if domain is None:
        return None

    cleaned = str(domain).strip()
    if not cleaned:
        return None

    if cleaned.lower() in {"agent", "default", "unknown", "none", "null"}:
        return None

    return cleaned

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )


def parse_datetime(value):
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    cleaned = str(value).strip()
    if not cleaned:
        return None

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue

    raise ValueError(f"Invalid datetime format: {value}")


def ensure_activity_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS activity (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100),
            email VARCHAR(150),
            domain VARCHAR(150),
            designation VARCHAR(150),
            role VARCHAR(50),
            app_name VARCHAR(150),
            action VARCHAR(50),
            start_time DATETIME,
            end_time DATETIME,
            login_time DATETIME,
            logout_time DATETIME,
            idle_time INT DEFAULT 0,
            screenshot_path LONGTEXT,
            app_url TEXT,
            duration INT,
            created_at DATETIME
        )
        """
    )

    expected_columns = {
        "email": "ALTER TABLE activity ADD COLUMN email VARCHAR(150)",
        "domain": "ALTER TABLE activity ADD COLUMN domain VARCHAR(150)",
        "designation": "ALTER TABLE activity ADD COLUMN designation VARCHAR(150)",
        "role": "ALTER TABLE activity ADD COLUMN role VARCHAR(50)",
        "app_name": "ALTER TABLE activity ADD COLUMN app_name VARCHAR(150)",
        "start_time": "ALTER TABLE activity ADD COLUMN start_time DATETIME",
        "end_time": "ALTER TABLE activity ADD COLUMN end_time DATETIME",
        "login_time": "ALTER TABLE activity ADD COLUMN login_time DATETIME",
        "logout_time": "ALTER TABLE activity ADD COLUMN logout_time DATETIME",
        "idle_time": "ALTER TABLE activity ADD COLUMN idle_time INT DEFAULT 0",
        "screenshot_path": "ALTER TABLE activity ADD COLUMN screenshot_path LONGTEXT",
        "app_url": "ALTER TABLE activity ADD COLUMN app_url TEXT",
        "duration": "ALTER TABLE activity ADD COLUMN duration INT",
        "created_at": "ALTER TABLE activity ADD COLUMN created_at DATETIME",
    }

    cursor.execute("SHOW COLUMNS FROM activity")
    existing_columns = {row[0] for row in cursor.fetchall()}

    for column_name, alter_sql in expected_columns.items():
        if column_name not in existing_columns:
            cursor.execute(alter_sql)


def ensure_user_admin_tables(cursor):
    for table in ["users", "admins"]:
        try:
            cursor.execute(f"SHOW COLUMNS FROM {table}")
            existing_columns = {row[0] for row in cursor.fetchall()}
            if "status" not in existing_columns:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN status VARCHAR(50) DEFAULT 'offline'")
            if "last_seen" not in existing_columns:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN last_seen DATETIME")
        except Exception:
            pass



def format_datetime(value):
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else None


def close_stale_sessions(cursor):
    """
    Close sessions that never received a logout because the agent stopped,
    lost network, or the machine went offline.
    """
    cutoff = datetime.now() - timedelta(seconds=ACTIVE_SESSION_TIMEOUT_SECONDS)

    cursor.execute(
        """
        SELECT
            s.id,
            s.username,
            COALESCE(MAX(COALESCE(e.created_at, e.end_time, e.start_time, e.login_time)), s.created_at, s.login_time) AS last_seen
        FROM activity s
        LEFT JOIN activity e
          ON LOWER(TRIM(e.username)) = LOWER(TRIM(s.username))
        WHERE s.app_name='system'
          AND s.action='session'
          AND s.logout_time IS NULL
        GROUP BY s.id, s.username, s.created_at, s.login_time
        HAVING last_seen IS NOT NULL AND last_seen < %s
        """,
        (cutoff,)
    )

    stale_sessions = cursor.fetchall()

    for row in stale_sessions:
        if isinstance(row, dict):
            session_id = row.get("id")
            username = row.get("username")
            last_seen = row.get("last_seen")
        else:
            session_id, username, last_seen = row

        cursor.execute(
            """
            UPDATE activity
            SET logout_time=%s,
                created_at=%s
            WHERE id=%s
              AND logout_time IS NULL
            """,
            (last_seen, last_seen, session_id)
        )

        cursor.execute(
            """
            UPDATE logs
            SET logout_time=%s,
                action='logout'
            WHERE LOWER(TRIM(username)) = LOWER(TRIM(%s))
              AND logout_time IS NULL
              AND (login_time IS NULL OR login_time <= %s)
            """,
            (last_seen, username, last_seen)
        )

        cursor.execute("UPDATE users SET status='offline', last_seen=%s WHERE username=%s", (last_seen, username))
        cursor.execute("UPDATE admins SET status='offline', last_seen=%s WHERE username=%s", (last_seen, username))


def mark_closed_logs_as_logout(cursor, username=None, email=None):
    username = (username or "").strip()
    email = (email or "").strip()

    if not username and not email:
        return

    cursor.execute(
        """
        UPDATE logs
        SET action='logout'
        WHERE logout_time IS NOT NULL
          AND COALESCE(action, '') <> 'logout'
          AND (
            (%s <> '' AND LOWER(TRIM(username)) = LOWER(TRIM(%s)))
            OR (%s <> '' AND LOWER(TRIM(email)) = LOWER(TRIM(%s)))
          )
        """,
        (username, username, email, email),
    )


@activity_bp.route("/api/activity", methods=["POST", "PATCH"])
def receive_activity():
    conn = None
    cursor = None
    try:
        data = request.get_json() or {}

        # Get all data from the agent's payload
        username = data.get("username")
        email = data.get("email")
        domain = normalize_domain(data.get("domain"))
        role = data.get("role")  # ✅ NEW: Capture role
        action = data.get("action")
        metadata = data.get("metadata", {})
        screenshot = metadata.get("screenshot")
        timestamp = parse_datetime(metadata.get("timestamp")) or datetime.now()
        login_time = parse_datetime(metadata.get("login_time")) or timestamp
        logout_time = parse_datetime(metadata.get("logout_time")) or timestamp
        idle_time = int(metadata.get("idle_time") or 0)
        designation = data.get("designation")

        if not username:
            return jsonify({"error": "Username not provided"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        ensure_activity_table(cursor)
        ensure_user_admin_tables(cursor)
        close_stale_sessions(cursor)
        mark_closed_logs_as_logout(cursor, username=username, email=email)

        if action in ["heartbeat", "screenshot", "login"]:
            cursor.execute("UPDATE users SET status='online', last_seen=%s WHERE username=%s", (timestamp, username))
            if cursor.rowcount == 0:
                cursor.execute("UPDATE admins SET status='online', last_seen=%s WHERE username=%s", (timestamp, username))
            
            # Force latest session to stay online (re-open if accidentally closed)
            cursor.execute("""
                UPDATE activity 
                SET logout_time = NULL 
                WHERE id = (
                    SELECT max_id FROM (
                        SELECT MAX(id) as max_id FROM activity 
                        WHERE username = %s AND action = 'session' AND app_name = 'system'
                    ) tmp
                )
            """, (username,))
            
        elif action == "logout":
            cursor.execute("UPDATE users SET status='offline', last_seen=%s WHERE username=%s", (timestamp, username))
            if cursor.rowcount == 0:
                cursor.execute("UPDATE admins SET status='offline', last_seen=%s WHERE username=%s", (timestamp, username))

        if action == "login":
            cursor.execute(
                """
                UPDATE activity
                SET logout_time=%s
                WHERE username=%s
                  AND app_name='system'
                  AND action='session'
                  AND logout_time IS NULL
                """,
                (timestamp, username)
            )

            cursor.execute(
                """
                UPDATE logs
                SET logout_time=%s,
                    action='logout'
                WHERE username=%s
                  AND logout_time IS NULL
                """,
                (timestamp, username)
            )

            cursor.execute(
                """
                INSERT INTO activity
                (username, email, domain, designation, role, app_name, action, login_time, idle_time, screenshot_path, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (username, email, domain, designation, role, "system", "session", login_time, idle_time, screenshot, timestamp)
            )
        elif action == "logout":
            cursor.execute(
                """
                UPDATE activity
                SET logout_time=%s,
                    idle_time=%s,
                    screenshot_path=COALESCE(%s, screenshot_path),
                    created_at=%s
                WHERE username=%s
                  AND app_name=%s
                  AND action=%s
                  AND logout_time IS NULL
                ORDER BY id DESC
                LIMIT 1
                """,
                (
                    logout_time,
                    idle_time,
                    screenshot,
                    timestamp,
                    username,
                    "system",
                    "session"
                )
            )
            activity_rowcount = cursor.rowcount

            cursor.execute(
                """
                UPDATE logs
                SET logout_time=%s,
                    action='logout'
                WHERE logout_time IS NULL
                  AND (
                    LOWER(TRIM(username)) = LOWER(TRIM(%s))
                    OR LOWER(TRIM(email)) = LOWER(TRIM(%s))
                  )
                ORDER BY id DESC
                LIMIT 1
                """,
                (logout_time, username or "", email or "")
            )

            if activity_rowcount == 0:
                cursor.execute(
                    """
                    INSERT INTO activity
                    (username, email, domain, designation, role, app_name, action, login_time, logout_time, idle_time, screenshot_path, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        username,
                        email,
                        domain,
                        designation,
                        role,
                        "system",
                        "session",
                        login_time,
                        logout_time,
                        idle_time,
                        screenshot,
                        timestamp
                    )
                )
        else:
            cursor.execute(
                """
                INSERT INTO activity
                (username, email, domain, designation, role, app_name, action, screenshot_path, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    username,
                    email,
                    domain,
                    designation,
                    role,
                    "system",
                    action,
                    screenshot,
                    timestamp
                )
            )

        conn.commit()

        return jsonify(
            {
                "message": "Activity logged successfully",
                "method": request.method
            }
        ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==============================
# GET LATEST LOGS FOR DASHBOARD
# ==============================

@activity_bp.route("/api/logs/latest", methods=["GET"])
def get_latest_logs():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        close_stale_sessions(cursor)
        conn.commit()
        
        cursor.execute(
            """
            SELECT l1.*
            FROM logs l1
            INNER JOIN (
                SELECT username, MAX(id) as latest_id
                FROM logs
                GROUP BY username
            ) l2 ON l1.id = l2.latest_id
            ORDER BY l1.login_time DESC
            """
        )
        logs = cursor.fetchall()
        
        return jsonify({"success": True, "logs": logs}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# ==============================
# GET USER STATUS (ONLINE/OFFLINE)
# ==============================

@activity_bp.route("/api/user-status", methods=["GET"])
def get_user_status():
    """
    Get the online/offline status of a user.
    Returns: { "username": "...", "status": "online|offline", "action": "login|logout", "login_time": "...", "last_activity": "..." }
    """
    conn = None
    cursor = None
    try:
        username = request.args.get("username")
        
        if not username:
            return jsonify({"error": "Username parameter required"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        close_stale_sessions(cursor)
        conn.commit()
        
        # Get the most recent session activity for this user
        cursor.execute(
            """
            SELECT id, username, email, domain, designation, login_time, logout_time, action, created_at
            FROM activity
            WHERE username=%s AND app_name='system' AND action='session'
            ORDER BY id DESC
            LIMIT 1
            """,
            (username,)
        )
        
        session_row = cursor.fetchone()
        
        if not session_row:
            return jsonify({
                "username": username,
                "status": "offline",
                "action": "login",
                "login_time": None,
                "last_activity": None
            }), 200
        
        # If logout_time is NULL, user is online
        is_online = session_row.get("logout_time") is None
        
        return jsonify({
            "username": username,
            "status": "online" if is_online else "offline",
            "action": "logout" if is_online else "login",
            "login_time": format_datetime(session_row.get("login_time")),
            "logout_time": format_datetime(session_row.get("logout_time")),
            "last_activity": format_datetime(session_row.get("created_at")),
            "email": session_row.get("email"),
            "domain": session_row.get("domain"),
            "designation": session_row.get("designation")
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==============================
# GET ALL ACTIVE USERS
# ==============================

@activity_bp.route("/api/active-users", methods=["GET"])
def get_active_users():
    """
    Get list of all users with their current status.
    Filters by role if provided (e.g., ?role=USER)
    """
    conn = None
    cursor = None
    try:
        role_filter = request.args.get("role")
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        close_stale_sessions(cursor)
        conn.commit()
        
        # Get latest session for each unique user
        query = """
            SELECT 
                a.username,
                a.email,
                a.domain,
                a.designation,
                a.role,
                a.login_time,
                a.logout_time,
                a.created_at,
                CASE WHEN a.logout_time IS NULL THEN 'online' ELSE 'offline' END as status,
                CASE WHEN a.logout_time IS NULL THEN 'logout' ELSE 'login' END as action
            FROM activity a
            INNER JOIN (
                SELECT username, MAX(id) as max_id
                FROM activity
                WHERE app_name='system' AND action='session'
                GROUP BY username
            ) latest ON a.id = latest.max_id
            WHERE a.app_name='system' AND a.action='session'
        """
        
        params = []
        if role_filter:
            query += " AND a.role=%s"
            params.append(role_filter)
        
        query += " ORDER BY a.login_time DESC"
        
        cursor.execute(query, params)
        users = cursor.fetchall()
        
        return jsonify({
            "total": len(users),
            "users": [
                {
                    "username": u.get("username"),
                    "email": u.get("email"),
                    "domain": u.get("domain"),
                    "designation": u.get("designation"),
                    "role": u.get("role"),
                    "status": u.get("status"),
                    "action": u.get("action"),
                    "login_time": format_datetime(u.get("login_time")),
                    "logout_time": format_datetime(u.get("logout_time")),
                    "last_activity": format_datetime(u.get("created_at"))
                }
                for u in users
            ]
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
