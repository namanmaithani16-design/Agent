# agent/api/client.py

import requests
from api.endpoints import APP_USAGE_URL

def send_app_usage(data):
    try:
        requests.post(APP_USAGE_URL, json=data, timeout=5)
    except Exception as e:
        print("[API ERROR]", e)
