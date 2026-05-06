import logging
import sys
import threading
import signal
import time

from ui.login_ui import LoginWindow
from ui.logout_ui import LogoutWindow
from background.worker import start_worker, stop_worker
from config import APP_NAME
from monitor.screenshot import capture_screenshot

# ✅ IMPORTANT
from utils.api_client import send_event
from storage.db import init_db, log_login, log_logout
from auth.session import get_current_user



# ================= LOGGING =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | MAIN | %(levelname)s | %(message)s"
)
logger = logging.getLogger("MAIN")


# ================= GLOBAL STATE =================
_monitoring_running = False
_shutdown_in_progress = False

_state_lock = threading.Lock()   # 🔹 upgrade: thread safety

_screenshot_thread = None
_screenshot_stop_event = threading.Event()

SCREENSHOT_INTERVAL = 60  # seconds

# Global variables for session IDs
_activity_id = None
_logs_id = None


# ================= SAFE SEND WRAPPER =================
def _safe_send_event(event_type, screenshot_path=None, username=None):
    try:
        send_event(event_type, screenshot_path, username)
        logger.info(f"{event_type} event sent")
    except Exception as e:
        logger.error(f"send_event failed ({event_type}): {e}")


# ================= SCREENSHOT LOOP =================
def _screenshot_loop():
    logger.info("Screenshot background loop started")

    while not _screenshot_stop_event.is_set():
        try:
            screenshot_path = capture_screenshot("interval")

            if screenshot_path:
                _safe_send_event("screenshot", screenshot_path)

        except Exception as e:
            logger.error(f"Periodic screenshot failed: {e}")

        _screenshot_stop_event.wait(SCREENSHOT_INTERVAL)

    logger.info("Screenshot loop stopped")


# ================= MONITORING CONTROL =================
def start_monitoring():
    global _monitoring_running

    with _state_lock:
        if _monitoring_running:
            return

        logger.info("Starting background monitoring")
        _monitoring_running = True

    threading.Thread(
        target=start_worker,
        daemon=True
    ).start()


def stop_monitoring():
    global _monitoring_running

    with _state_lock:
        if not _monitoring_running:
            return

        logger.info("Stopping monitoring")

        try:
            stop_worker()
        except Exception as e:
            logger.error(f"Error stopping worker: {e}")

        _monitoring_running = False


# ================= CLEAN SHUTDOWN =================
def shutdown(exit_code=0):
    global _shutdown_in_progress

    with _state_lock:
        if _shutdown_in_progress:
            return
        _shutdown_in_progress = True

    logger.info("Shutting down Employee Agent")

    _screenshot_stop_event.set()
    stop_monitoring()

    time.sleep(1)  # 🔹 small delay for clean thread exit
    sys.exit(exit_code)


# ================= CALLBACKS =================
def on_login_success():
    global _activity_id, _logs_id

    current_user = get_current_user()
    if not current_user:
        logger.error("on_login_success called, but no user is in session!")
        return

    username = current_user.get("username")
    logger.info(f"Login successful for user: {username}")

    # Log to database
    _activity_id, _logs_id = log_login()

    # 🔹 Send login event
    try:
        screenshot_path = capture_screenshot("login")
        if screenshot_path:
            _safe_send_event("login", screenshot_path, username)
    except Exception:
        logger.exception("Failed to send login event")

    # 🔹 Start monitoring
    start_monitoring()

    # 🔹 Start screenshot thread
    global _screenshot_thread
    _screenshot_stop_event.clear()

    if _screenshot_thread is None or not _screenshot_thread.is_alive():
        _screenshot_thread = threading.Thread(
            target=_screenshot_loop,
            daemon=True
        )
        _screenshot_thread.start()

    # 🔹 Open logout window
    LogoutWindow(on_logout=on_logout)


def on_logout():
    global _activity_id, _logs_id
    logger.info("Employee logout initiated")

    # Log logout to database
    if _activity_id is not None or _logs_id is not None:
        log_logout(_activity_id, _logs_id)

    try:
        screenshot_path = capture_screenshot("logout")
        if screenshot_path:
            _safe_send_event("logout", screenshot_path)
    except Exception:
        logger.exception("Failed to send logout event")

    shutdown(0)


# ================= SIGNAL HANDLING =================
def _handle_signal(signum, frame):
    logger.warning(f"System signal received: {signum}")
    shutdown(0)


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


# ================= MAIN =================
def main():
    logger.info(f"{APP_NAME} starting")

    # Initialize database
    init_db()
     

    try:
        login_window = LoginWindow(on_success=on_login_success)
        login_window.run()
    except Exception as e:
        logger.exception(f"Fatal error in main loop: {e}")
        shutdown(1)


if __name__ == "__main__":
    main()
