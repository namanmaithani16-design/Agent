import requests
import base64
from datetime import datetime

SERVER_URL = "http://127.0.0.1:5000/api/activity"

def send_event(action, screenshot_path=None):

    screenshot_base64 = None

    if screenshot_path:
        with open(screenshot_path, "rb") as img:
            screenshot_base64 = base64.b64encode(
                img.read()
            ).decode("utf-8")

    payload = {
        "username": "naman",          # REQUIRED
        "action": action,             # REQUIRED
        "metadata": {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "screenshot": screenshot_base64
        }
    }

    print("📤 PAYLOAD:", payload)

    response = requests.post(SERVER_URL, json=payload)

    print("send", response.status_code)
    print("Server:", response.text)
