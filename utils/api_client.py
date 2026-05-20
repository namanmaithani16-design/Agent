# agent/utils/api_client.py

import base64
from datetime import datetime

import requests

from auth.session import get_current_user, normalize_domain
from storage.db import get_open_session_activity

SERVER_URL = "http://127.0.0.1:5000/api/activity"


def send_event(action, screenshot_path=None, username=None, metadata=None):
    screenshot_base64 = None

    if screenshot_path:
        try:
            with open(screenshot_path, "rb") as img:
                screenshot_base64 = base64.b64encode(img.read()).decode("utf-8")
        except Exception as e:
            print(f"[API] Could not read screenshot: {e}")

    current_user = get_current_user()
    if current_user:
        username = current_user.get("username")
        email = current_user.get("email")
        domain = normalize_domain(current_user.get("domain"))
        designation = current_user.get("designation")
        role = current_user.get("role")
    else:
        print("[API] No active session found when sending event")
        username = "unknown"
        email = None
        domain = None
        designation = None
        role = None

    session_row = None
    if action in {"login", "logout"} and username != "unknown":
        try:
            session_row = get_open_session_activity(username)
        except Exception as e:
            print(f"[API] Could not fetch session row: {e}")

    base_metadata = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "screenshot": screenshot_base64,
    }

    if metadata:
        base_metadata.update(metadata)

    payload = {
        "username": username,
        "email": email,
        "domain": domain,
        "designation": designation,
        "role": role,
        "action": action,
        "metadata": base_metadata,
    }

    if session_row:
        payload["metadata"]["login_time"] = (
            session_row["login_time"].strftime("%Y-%m-%d %H:%M:%S")
            if session_row.get("login_time") else None
        )
        payload["metadata"]["idle_time"] = int(session_row.get("idle_time") or 0)

    if action == "logout":
        payload["metadata"]["logout_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"[API] Sending '{action}' event for user '{username}'")
    print("[API] PAYLOAD:", payload)

    try:
        request_method = requests.patch if action == "logout" else requests.post
        response = request_method(SERVER_URL, json=payload, timeout=10)
        print(f"[API] Response status: {response.status_code}")
        print(f"[API] Response body: {response.text}")
        return response
    except requests.exceptions.ConnectionError:
        print(f"[API] Cannot connect to server at {SERVER_URL}")
        print("[API] Make sure your Flask backend is running")
        return None
    except requests.exceptions.Timeout:
        print(f"[API] Request timed out for action '{action}'")
        return None
    except Exception as e:
        print(f"[API] Unexpected error: {e}")
        return None
