import time
import ctypes
import json
import re
import psutil
from datetime import datetime, timezone, timedelta

from auth.session import is_active, get_current_user
from storage.db import ensure_mysql_activity_table, get_mysql_connection, init_db

try:
    import win32gui
    import win32process
except Exception:
    win32gui = None
    win32process = None

try:
    from pywinauto import Application
except Exception:
    Application = None


user32 = ctypes.windll.user32
IST = timezone(timedelta(hours=5, minutes=30))
BROWSER_PROCESSES = {
    "chrome.exe",
    "msedge.exe",
    "brave.exe",
    "firefox.exe",
    "opera.exe",
    "opera_gx.exe",
}
URL_RE = re.compile(
    r"^(?:https?://)?(?:www\.)?[a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)+(?:[/:?#].*)?$",
    re.IGNORECASE,
)


def now_ist():
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


# ==========================================
# GET CURRENT FOREGROUND APPLICATION
# ==========================================

def normalize_url(value):
    if not value:
        return None

    value = str(value).strip()
    if not value or " " in value:
        return None

    if not URL_RE.match(value):
        return None

    if not value.lower().startswith(("http://", "https://")):
        value = f"https://{value}"

    return value


def get_foreground_window_info():

    hwnd = user32.GetForegroundWindow()

    if not hwnd:
        return None

    if win32process:
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
        except Exception:
            pid = None
    else:
        pid_ref = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_ref))
        pid = pid_ref.value

    if win32gui:
        try:
            title = win32gui.GetWindowText(hwnd)
        except Exception:
            title = ""
    else:
        title = ""

    try:
        process = psutil.Process(pid)
        app_name = process.name()
    except Exception:
        app_name = None

    return {
        "hwnd": hwnd,
        "pid": pid,
        "app_name": app_name,
        "window_title": title,
    }


def get_browser_url(pid):
    if not Application or not pid:
        return None

    try:
        app = Application(backend="uia").connect(process=pid, timeout=1)
        window = app.top_window()
    except Exception:
        return None

    try:
        controls = window.descendants(control_type="Edit")
    except Exception:
        return None

    for control in controls:
        candidates = []
        try:
            candidates.append(control.window_text())
        except Exception:
            pass
        try:
            value_pattern = control.iface_value
            candidates.append(value_pattern.CurrentValue)
        except Exception:
            pass

        for candidate in candidates:
            url = normalize_url(candidate)
            if url:
                return url

    return None


def get_current_activity():
    info = get_foreground_window_info()
    if not info:
        return None

    app_name = info.get("app_name")
    app_url = None

    if app_name and app_name.lower() in BROWSER_PROCESSES:
        app_url = get_browser_url(info.get("pid"))

    return {
        "app_name": app_name,
        "window_title": info.get("window_title") or "",
        "app_url": app_url,
    }


# ==========================================
# SAVE APP USAGE TO DATABASE
# ==========================================

def build_activity_metadata(window_title, app_url):
    return json.dumps(
        {
            "window_title": window_title,
            "app_url": app_url,
            "source": "foreground_monitor",
        }
    )


def create_app_usage(user, activity, start):
    conn = None
    cur = None
    app_name = activity.get("app_name") or "unknown"
    window_title = activity.get("window_title") or None
    app_url = activity.get("app_url") or None
    metadata = build_activity_metadata(window_title, app_url)

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
            (username, email, domain, designation, role, app_name, action, start_time, end_time,
             duration, login_time, app_url, window_title, metadata, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user.get("username"),
                user.get("email"),
                user.get("domain"),
                user.get("designation"),
                user.get("role"),
                app_name,
                "app_usage",
                start,
                start,
                0,
                now_ist(),
                app_url,
                window_title,
                metadata,
                now_ist(),
            )
        )

        activity_id = cur.lastrowid
        conn.commit()
        url_suffix = f" | {app_url}" if app_url else ""
        print(f"[APP USAGE] Started: {app_name}{url_suffix} for '{user.get('username')}'")
        return activity_id

    except Exception as e:
        print("[APP USAGE] DB Error:", e)
        return None

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def update_app_usage(activity_id, end, duration):
    if not activity_id:
        return

    conn = None
    cur = None

    try:
        conn = get_mysql_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE activity
            SET end_time = %s,
                duration = %s,
                created_at = %s
            WHERE id = %s
            """,
            (end, duration, now_ist(), activity_id),
        )
        conn.commit()
        print(f"[APP USAGE] Updated id={activity_id} ({duration}s)")

    except Exception as e:
        print("[APP USAGE] Update Error:", e)

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
    current_activity_id = None

    session_user = get_current_user()

    if not session_user:
        print("[APP USAGE] Monitor cannot start: No user session.")
        return

    username = session_user.get("username")

    print(f"[APP USAGE] Monitoring started for user: {username}")

    while is_active():

        activity = get_current_activity()
        now = datetime.now()

        if activity != current_app:
            if current_app and start_time:
                duration = int((now - start_time).total_seconds())

                if duration > 0:
                    print(
                        f"[APP USAGE] {current_app.get('app_name')} "
                        f"{start_time.strftime('%H:%M:%S')} -> "
                        f"{now.strftime('%H:%M:%S')} "
                        f"({duration}s)"
                    )

                    update_app_usage(current_activity_id, now, duration)

            current_app = activity
            start_time = now
            current_activity_id = (
                create_app_usage(session_user, current_app, start_time)
                if current_app else None
            )
        elif current_app and start_time:
            duration = int((now - start_time).total_seconds())
            update_app_usage(current_activity_id, now, duration)

        time.sleep(poll_interval)

    if current_app and start_time:
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())
        if duration > 0:
            update_app_usage(current_activity_id, end_time, duration)

    print(f"[APP USAGE] Monitoring stopped for user: {username}")
