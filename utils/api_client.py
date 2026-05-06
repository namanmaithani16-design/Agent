import requests
import base64
from datetime import datetime
from auth.session import get_current_user, normalize_domain
from storage.db import get_open_session_activity

SERVER_URL = "http://127.0.0.1:5000/api/activity"

def send_event(action, screenshot_path=None, username=None):

    screenshot_base64 = None

    if screenshot_path:
        with open(screenshot_path, "rb") as img:
            screenshot_base64 = base64.b64encode(
                img.read()
            ).decode("utf-8")

    # Get current logged-in user from session
    current_user = get_current_user()
    if current_user:
        username = current_user.get("username")
        email = current_user.get("email")
        domain = normalize_domain(current_user.get("domain"))
        designation = current_user.get("designation")
    else:
        username = "unknown"
        email = None
        domain = None
        designation = None

    session_row = None
    if action in {"login", "logout"} and username != "unknown":
        session_row = get_open_session_activity(username)

    payload = {
        "username": username,
        "email": email,
        "domain": domain,
        "designation": designation,
        "action": action,
        "metadata": {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "screenshot": screenshot_base64
        }
    }

    if session_row:
        payload["metadata"]["login_time"] = (
            session_row["login_time"].strftime("%Y-%m-%d %H:%M:%S")
            if session_row.get("login_time") else None
        )
        payload["metadata"]["idle_time"] = int(session_row.get("idle_time") or 0)

    if action == "logout":
        payload["metadata"]["logout_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("📤 PAYLOAD:", payload)

    request_method = requests.patch if action == "logout" else requests.post
    response = request_method(SERVER_URL, json=payload)

    print("send", response.status_code)
    print("Server:", response.text)
