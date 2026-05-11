# agent/ui/tray.py

import pystray
from PIL import Image
import threading

# global flag
logout_requested = False


def on_logout(icon, item):
    global logout_requested
    logout_requested = True
    icon.stop()   # tray band karo

def on_view_tasks(icon, item):
    from ui.tasks_ui import TasksWindow
    threading.Thread(target=TasksWindow, daemon=True).start()


def run_tray():
    image = Image.new("RGB", (64, 64), color=(79, 115, 136))

    icon = pystray.Icon(
        "ISMS",
        image,
        "ISMS Monitoring Active",
        menu=pystray.Menu(
            pystray.MenuItem("View Tasks", on_view_tasks),
            pystray.MenuItem("Logout", on_logout)
        )
    )

    icon.run()
    return logout_requested
