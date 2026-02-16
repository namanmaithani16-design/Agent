import logging
import sys
import threading
import signal

from ui.login_ui import LoginWindow
from ui.logout_ui import LogoutWindow
from background.worker import start_worker, stop_worker
from config import APP_NAME
from monitor.screenshot import capture_screenshot

# ✅ IMPORTANT
from utils.api_client import send_event


# ================= LOGGING =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | MAIN | %(levelname)s | %(message)s"
)
logger = logging.getLogger("MAIN")


# ================= GLOBAL STATE =================
_monitoring_running = False
_shutdown_in_progress = False

_screenshot_thread = None
_screenshot_stop_event = threading.Event()

SCREENSHOT_INTERVAL = 60  # seconds


# ================= SCREENSHOT LOOP =================
def _screenshot_loop():
    logger.info("Screenshot background loop started")

    while not _screenshot_stop_event.is_set():
        try:
            screenshot_path = capture_screenshot("interval")

            if screenshot_path:
                try:
                    send_event("screenshot", screenshot_path)
                except Exception as e:
                    logger.error(f"send_event failed: {e}")

        except Exception as e:
            logger.error(f"Periodic screenshot failed: {e}")

        _screenshot_stop_event.wait(SCREENSHOT_INTERVAL)

    logger.info("Screenshot loop stopped")


# ================= MONITORING CONTROL =================
def start_monitoring():
    global _monitoring_running

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

    if not _monitoring_running:
        return

    logger.info("Stopping monitoring")
    stop_worker()
    _monitoring_running = False


# ================= CLEAN SHUTDOWN =================
def shutdown(exit_code=0):
    global _shutdown_in_progress

    if _shutdown_in_progress:
        return

    _shutdown_in_progress = True
    logger.info("Shutting down Employee Agent")

    _screenshot_stop_event.set()
    stop_monitoring()

    sys.exit(exit_code)


# ================= CALLBACKS =================
def on_login_success(username):
    logger.info(f"Login successful for user: {username}")

    # 🔹 Send login event
    try:
        screenshot_path = capture_screenshot("login")
        if screenshot_path:
            send_event("login", screenshot_path)
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
    logger.info("Employee logout initiated")

    try:
        screenshot_path = capture_screenshot("logout")
        if screenshot_path:
            send_event("logout", screenshot_path)
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

    login_window = LoginWindow(on_success=on_login_success)
    login_window.run()


if __name__ == "__main__":
    main()
