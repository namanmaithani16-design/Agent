# agent/monitor/app_usage.py

from getpass import getuser
import time
import ctypes
import psutil
from datetime import datetime
from auth.session import is_active, get_current_user
from storage.db import get_connection

user32 = ctypes.windll.user32


def get_foreground_process():
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None

    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

    try:
        return psutil.Process(pid.value).name()
    except Exception:
        return None


def save_app_usage(user, app, start, end, duration):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO app_usage (user_id, app_name, start_time, end_time, duration)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user,
        app,
        start.isoformat(),
        end.isoformat(),
        duration
    ))

    conn.commit()
    conn.close()


def app_usage_monitor(poll_interval=5):
    current_app = None
    start_time = None
    user = getuser()

    while is_active():
        app = get_foreground_process()
        now = datetime.now()

        if app != current_app:
            if current_app and start_time:
                duration = (now - start_time).seconds

                print(
                    f"[APP USAGE] {current_app} "
                    f"{start_time.strftime('%H:%M:%S')} → "
                    f"{now.strftime('%H:%M:%S')} "
                    f"({duration}s)"
                )

                save_app_usage(
                    user=user,
                    app=current_app,
                    start=start_time,
                    end=now,
                    duration=duration
                )

            current_app = app
            start_time = now

        time.sleep(poll_interval)
