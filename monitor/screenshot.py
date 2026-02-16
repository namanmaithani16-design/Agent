# agent/monitor/screenshot.py

import os
import threading
from datetime import datetime
import logging

try:
    import pyautogui
except Exception as e:
    pyautogui = None
    print(f"[PYAutoGUI IMPORT ERROR] {e}")

logger = logging.getLogger("SCREENSHOT")

# ================= BASE DIRECTORY =================
BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "storage",
    "screenshots"
)

# Thread lock (important for background thread safety)
_screenshot_lock = threading.Lock()

# Ensure folder exists
try:
    os.makedirs(BASE_DIR, exist_ok=True)
except Exception as e:
    logger.error(f"Screenshot directory creation failed: {e}")


# ================= CORE FUNCTION =================
def capture_screenshot(prefix: str = "capture"):
    """
    Safe screenshot capture function.
    """

    if pyautogui is None:
        logger.error("pyautogui not available")
        return None

    with _screenshot_lock:  # thread safety
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{timestamp}.png"
            filepath = os.path.join(BASE_DIR, filename)

            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)

            print(f"[SCREENSHOT SAVED] {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None


# ================= BACKWARD COMPATIBILITY =================
def capture_login():
    return capture_screenshot("login")


def capture_logout():
    return capture_screenshot("logout")


def capture_hourly():
    return capture_screenshot("hourly")


def capture_interval():
    return capture_screenshot("interval")
