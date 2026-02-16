# agent/background/worker.py

import threading
import time
from monitor.screenshot import capture_hourly
from monitor.idle import idle_monitor
from monitor.app_usage import app_usage_monitor
from auth.session import is_active

_worker = None
_idle_thread = None
_app_thread = None
_running = False


def start_worker():
    global _worker, _idle_thread, _app_thread, _running

    if _running:
        return

    _running = True

    # Hourly screenshot
    _worker = threading.Thread(target=_run, daemon=True)
    _worker.start()

    # Idle monitor
    _idle_thread = threading.Thread(
        target=idle_monitor,
        daemon=True
    )
    _idle_thread.start()

    # App usage monitor
    _app_thread = threading.Thread(
        target=app_usage_monitor,
        daemon=True
    )
    _app_thread.start()

    print("[WORKER] Monitoring started")


def _run():
    while is_active():
        time.sleep(3600)
        if is_active():
            capture_hourly()


def stop_worker():
    global _running
    _running = False
    print("[WORKER] Monitoring stopped")
