from flask import Blueprint, request, jsonify
import mysql.connector
from datetime import datetime
from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

activity_bp = Blueprint("activity_bp", __name__)


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

        if action == "login":
            cursor.execute(
                """
                INSERT INTO activity
                (username, email, domain, designation, app_name, action, login_time, idle_time, screenshot_path, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    username,
                    email,
                    domain,
                    designation,
                    "system",
                    "session",
                    login_time,
                    idle_time,
                    screenshot,
                    timestamp
                )
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

            if cursor.rowcount == 0:
                cursor.execute(
                    """
                    INSERT INTO activity
                    (username, email, domain, designation, app_name, action, login_time, logout_time, idle_time, screenshot_path, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        username,
                        email,
                        domain,
                        designation,
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
                (username, email, domain, designation, app_name, action, screenshot_path, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    username,
                    email,
                    domain,
                    designation,
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
