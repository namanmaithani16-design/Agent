# agent/monitor/idle.py

import ctypes
import time
from datetime import datetime
from auth.session import is_active
from storage.db import log_idle_time


# Windows API structure
class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
    ]


def get_idle_seconds():
    """
    Returns idle time in seconds (accurate)
    """
    last_input_info = LASTINPUTINFO()
    last_input_info.cbSize = ctypes.sizeof(LASTINPUTINFO)

    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input_info))

    # Use GetTickCount64 to avoid overflow issue
    tick_count = ctypes.windll.kernel32.GetTickCount64()
    millis = tick_count - last_input_info.dwTime

    return millis / 1000.0


def idle_monitor(idle_limit=5):
    """
    idle_limit = 120 seconds (2 minutes)
    """
    idle_start = None
    is_idle = False

    print("Idle monitor started... (Idle limit: 2 minutes)")

    while is_active():
        try:
            idle_seconds = get_idle_seconds()

            # USER BECOMES IDLE
            if idle_seconds >= idle_limit:
                if not is_idle:
                    is_idle = True
                    idle_start = datetime.now()
                    print(f"[IDLE START] {idle_start}")

            # USER BECOMES ACTIVE AGAIN
            else:
                if is_idle:
                    idle_end = datetime.now()
                    duration = (idle_end - idle_start).total_seconds()

                    print(f"[IDLE END] {idle_end} | Duration: {int(duration)}s")

                    log_idle_time(duration)

                    is_idle = False
                    idle_start = None

            time.sleep(5)

        except Exception as e:
            print("Idle monitor error:", e)
            time.sleep(5)

    # If session ends while user is idle
    if is_idle and idle_start:
        idle_end = datetime.now()
        duration = (idle_end - idle_start).total_seconds()
        print(f"[SESSION END - IDLE] Duration: {int(duration)}s")
        log_idle_time(duration)
