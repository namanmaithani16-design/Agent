import mysql.connector
from datetime import datetime
from auth.session import get_current_user, normalize_domain
from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


# ==============================
# MYSQL RDS CONFIG
# ==============================

def get_connection():

    try:

        print("=================================")
        print("CONNECTING TO MYSQL RDS DATABASE")
        print("HOST:", DB_HOST)
        print("DATABASE:", DB_NAME)
        print("=================================")

        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )

        print("✅ MySQL connection SUCCESS")

        return conn

    except Exception as e:

        print("❌ MySQL Connection Error:", e)
        return None


# ==============================
# DATABASE INITIALIZATION
# ==============================

def init_db():

    conn = get_connection()

    if not conn:
        print("❌ Cannot initialize database")
        return

    cur = conn.cursor()

    # ------------------------------
    # USERS TABLE
    # ------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE,
            password TEXT,
            role VARCHAR(50),
            email VARCHAR(150),
            domain VARCHAR(150),
            designation VARCHAR(150)
        )
    """)

    # ------------------------------
    # TASKS TABLE
    # ------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100),
            title VARCHAR(200),
            description TEXT,
            status VARCHAR(50) DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ------------------------------
    # LOGS TABLE (LOGIN SESSIONS)
    # ------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            username VARCHAR(100),
            email VARCHAR(150),
            domain VARCHAR(150),
            role VARCHAR(50),
            designation VARCHAR(150),
            action VARCHAR(50),
            login_time DATETIME,
            logout_time DATETIME
        )
    """)

    # ------------------------------
    # ACTIVITY TABLE (APP / SCREENSHOT / URL)
    # ------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS activity (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100),
            app_name VARCHAR(150),
            action VARCHAR(50),
            start_time DATETIME,
            end_time DATETIME,
            login_time DATETIME,
            logout_time DATETIME,
            idle_time INT DEFAULT 0,
            screenshot_path TEXT,
            app_url TEXT,
            duration INT,
            created_at DATETIME
        )
    """)

    activity_columns = {
        "start_time": "ALTER TABLE activity ADD COLUMN start_time DATETIME",
        "end_time": "ALTER TABLE activity ADD COLUMN end_time DATETIME",
        "login_time": "ALTER TABLE activity ADD COLUMN login_time DATETIME",
        "logout_time": "ALTER TABLE activity ADD COLUMN logout_time DATETIME",
        "idle_time": "ALTER TABLE activity ADD COLUMN idle_time INT DEFAULT 0",
    }

    cur.execute("SHOW COLUMNS FROM activity")
    existing_activity_columns = {row[0] for row in cur.fetchall()}

    for column_name, alter_sql in activity_columns.items():
        if column_name not in existing_activity_columns:
            cur.execute(alter_sql)

    conn.commit()
    conn.close()

    print("✅ Database tables verified / created")


# ==============================
# LOGIN LOGGING
# ==============================

def log_login():

    conn = get_connection()

    if not conn:
        raise Exception("Database connection failed")

    cur = conn.cursor()

    login_time = datetime.now()

    current_user = get_current_user()

    if not current_user:
        conn.close()
        raise Exception("No user session found")

    user_id = current_user.get("user_id")
    username = current_user.get("username")
    email = current_user.get("email")
    domain = normalize_domain(current_user.get("domain"))
    role = current_user.get("role")
    designation = current_user.get("designation")

    print("Logging login for:", username)

    cur.execute(
        """
        INSERT INTO activity
        (username, app_name, action, login_time, idle_time, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (username, "system", "session", login_time, 0, login_time)
    )

    activity_id = cur.lastrowid

    # Store session timing in the logs table only, so login appears once.
    cur.execute(
        """
        INSERT INTO logs 
        (user_id, username, email, domain, role, designation, action, login_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            user_id,
            username,
            email,
            domain,
            role,
            designation,
            "login",
            login_time
        )
    )

    logs_id = cur.lastrowid

    conn.commit()
    conn.close()

    print("✅ Login recorded:", login_time)

    return activity_id, logs_id


# ==============================
# LOGOUT LOGGING
# ==============================

def log_logout(activity_id, logs_id):

    conn = get_connection()

    if not conn:
        raise Exception("Database connection failed")

    cur = conn.cursor()

    logout_time = datetime.now()
    current_user = get_current_user()

    if current_user and activity_id is not None:
        cur.execute(
            """
            UPDATE activity
            SET logout_time=%s
            WHERE id=%s
            """,
            (logout_time, activity_id)
        )

    if logs_id is not None:
        cur.execute(
            """
            UPDATE logs
            SET logout_time=%s, action=%s
            WHERE id=%s
            """,
            (logout_time, "logout", logs_id)
        )

    conn.commit()
    conn.close()

    print("✅ Logout recorded:", logout_time)


# ==============================
# IDLE TIME LOG
# ==============================

def log_idle_time(duration):
    """
    Records an idle period in the activity table.
    """
    conn = get_connection()
    if not conn:
        print("❌ [IDLE LOG] Database connection failed")
        return

    current_user = get_current_user()
    if not current_user:
        if conn and conn.is_connected():
            conn.close()
        return

    username = current_user.get("username")
    now = datetime.now()
    cur = None
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, COALESCE(idle_time, 0)
            FROM activity
            WHERE username=%s AND app_name=%s AND action=%s AND logout_time IS NULL
            ORDER BY id DESC
            LIMIT 1
            """,
            (username, "system", "session")
        )
        session_row = cur.fetchone()

        if not session_row:
            print("❌ [IDLE LOG] No open session row found in activity")
            return

        session_activity_id, existing_idle_time = session_row
        cur.execute(
            """
            UPDATE activity
            SET idle_time=%s, created_at=%s
            WHERE id=%s
            """,
            (existing_idle_time + int(duration), now, session_activity_id)
        )
        conn.commit()
        print(f"✅ Idle time updated: {existing_idle_time + int(duration)}s")
    except Exception as e:
        print(f"❌ [IDLE LOG] DB Error: {e}")
    finally:
        if cur:
            cur.close()
        if conn and conn.is_connected():
            conn.close()


def get_open_session_activity(username=None):
    """
    Returns the latest open session row for the current user.
    """
    conn = get_connection()
    if not conn:
        return None

    current_user = get_current_user()
    if not username and current_user:
        username = current_user.get("username")

    if not username:
        if conn and conn.is_connected():
            conn.close()
        return None

    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, username, login_time, logout_time, COALESCE(idle_time, 0) AS idle_time
            FROM activity
            WHERE username=%s AND app_name=%s AND action=%s AND logout_time IS NULL
            ORDER BY id DESC
            LIMIT 1
            """,
            (username, "system", "session")
        )
        return cur.fetchone()
    except Exception as e:
        print(f"❌ [SESSION FETCH] DB Error: {e}")
        return None
    finally:
        if cur:
            cur.close()
        if conn and conn.is_connected():
            conn.close()


# ==============================
# SCREENSHOT / ACTIVITY LOG
# ==============================

def log_activity(action, app_name=None, screenshot_path=None, url=None):

    conn = get_connection()

    if not conn:
        raise Exception("Database connection failed")

    cur = conn.cursor()

    now = datetime.now()

    current_user = get_current_user()

    if not current_user:
        conn.close()
        return

    username = current_user.get("username")

    cur.execute(
        """
        INSERT INTO activity
        (username, app_name, action, screenshot_path, app_url, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            username,
            app_name,
            action,
            screenshot_path,
            url,
            now
        )
    )

    conn.commit()
    conn.close()

    print("✅ Activity recorded:", action)


# ==============================
# FETCH ASSIGNED TASKS
# ==============================

def get_user_tasks():
    """
    Retrieves the assigned tasks for the currently logged-in user.
    """
    conn = get_connection()
    
    if not conn:
        return []

    current_user = get_current_user()
    if not current_user:
        if conn: conn.close()
        return []

    username = current_user.get("username")
    tasks = []
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id, title, description, status, created_at FROM tasks WHERE username=%s ORDER BY created_at DESC",
            (username,)
        )
        tasks = cur.fetchall()
    except Exception as e:
        print(f"❌ [TASKS FETCH] DB Error: {e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()
        
    return tasks
