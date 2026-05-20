import time
import ctypes
import psutil
from datetime import datetime, timezone, timedelta

from auth.session import is_active, get_current_user
from storage.db import ensure_mysql_activity_table, get_mysql_connection, init_db


user32 = ctypes.windll.user32
IST = timezone(timedelta(hours=5, minutes=30))


def now_ist():
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


# ==========================================
# GET CURRENT FOREGROUND APPLICATION
# ==========================================

def get_foreground_process():

    hwnd = user32.GetForegroundWindow()

    if not hwnd:
        return None

    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

    try:
        process = psutil.Process(pid.value)
        return process.name()
    except Exception:
        return None


# ==========================================
# SAVE APP USAGE TO DATABASE
# ==========================================

def save_app_usage(user, app, start, end, duration):

    conn = None
    cur = None

    try:
        conn = get_mysql_connection()

        if not conn:
            print("[APP USAGE] Database connection failed")
            return

        cur = conn.cursor()
        ensure_mysql_activity_table(cur)

        cur.execute(
            """
            INSERT INTO activity
            (username, email, domain, designation, role, app_name, action, start_time, end_time, duration, login_time, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user.get("username"),
                user.get("email"),
                user.get("domain"),
                user.get("designation"),
                user.get("role"),
                app,
                "app_usage",
                start,
                end,
                duration,
                now_ist(),
                now_ist(),
            )
        )

        conn.commit()
        print(f"[APP USAGE] Saved: {app} ({duration}s) for '{user.get('username')}'")

    except Exception as e:
        print("[APP USAGE] DB Error:", e)

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# ==========================================
# APP USAGE MONITOR LOOP
# ==========================================

def app_usage_monitor(poll_interval=5):

    # Ensure database tables exist
    init_db()

    current_app = None
    start_time = None

    session_user = get_current_user()

    if not session_user:
        print("[APP USAGE] Monitor cannot start: No user session.")
        return

    username = session_user.get("username")

    print(f"[APP USAGE] Monitoring started for user: {username}")

    while is_active():

        app = get_foreground_process()
        now = datetime.now()

        if app != current_app:

            if current_app and start_time:

                duration = int((now - start_time).total_seconds())

                print(
                    f"[APP USAGE] {current_app} "
                    f"{start_time.strftime('%H:%M:%S')} -> "
                    f"{now.strftime('%H:%M:%S')} "
                    f"({duration}s)"
                )

                save_app_usage(
                    user=session_user,
                    app=current_app,
                    start=start_time,
                    end=now,
                    duration=duration
                )

            current_app = app
            start_time = now

        time.sleep(poll_interval)

    print(f"[APP USAGE] Monitoring stopped for user: {username}")
