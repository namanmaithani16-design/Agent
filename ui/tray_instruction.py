# agent/ui/tray_instruction.py

import tkinter as tk
import os

FLAG_FILE = "storage/.tray_instruction_shown"


def show_tray_instruction():
    # Agar pehle hi dikhaya ja chuka hai → dobara mat dikhao
    if os.path.exists(FLAG_FILE):
        return

    root = tk.Tk()
    root.title("ISMS Notice")
    root.geometry("450x220")
    root.resizable(False, False)

    msg = (
        "ISMS is now running in the background.\n\n"
        "🔔 IMPORTANT:\n"
        "1. Click the ^ arrow in the taskbar\n"
        "2. Find the ISMS icon\n"
        "3. Drag it outside for easy access\n\n"
        "You can logout anytime from the tray icon."
    )

    tk.Label(
        root,
        text=msg,
        font=("Arial", 11),
        justify="left",
        padx=20,
        pady=20
    ).pack()

    def close_popup():
        # Flag file bana do → next time popup nahi aayega
        os.makedirs("storage", exist_ok=True)
        with open(FLAG_FILE, "w") as f:
            f.write("shown")
        root.destroy()

    tk.Button(
        root,
        text="Got it",
        width=15,
        bg="#2ecc71",
        fg="white",
        command=close_popup
    ).pack(pady=10)

    root.mainloop()
