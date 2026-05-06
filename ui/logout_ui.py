# agent/ui/logout_ui.py

import tkinter as tk
from tkinter import messagebox
import threading
from auth.login import logout_user
from storage.db import get_user_tasks


class LogoutWindow:
    def __init__(self, on_logout=None):
        self.on_logout = on_logout

        self.root = tk.Tk()
        self.root.title("ISMS Logout")
        self.root.state("zoomed")  # Full screen

        # Prevent automatic logout on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.build_ui()
        self.root.mainloop()

    def on_close(self):
        # Automatically logout if the intern directly closes the window
        if self.on_logout:
            self.on_logout()
            
        logout_user()
        self.root.destroy()

    def build_ui(self):
        container = tk.Frame(self.root)
        container.pack(fill="both", expand=True)

        # LEFT PANEL
        left = tk.Frame(container, bg="#4f7388")
        left.pack(side="left", fill="both", expand=True)

        # RIGHT PANEL
        right = tk.Frame(container, bg="#ffffff")
        right.pack(side="right", fill="both", expand=True)

        # -------- LEFT CONTENT --------
        tk.Label(
            left,
            text="ISMS Logout",
            bg="#4f7388",
            fg="white",
            font=("Arial", 28, "bold")
        ).pack(pady=(80, 20))

        tk.Label(
            left,
            text="You are about to logout",
            bg="#4f7388",
            fg="white",
            font=("Arial", 12)
        ).pack(pady=10)

        tk.Label(
            left,
            text="Monitoring will stop after logout",
            bg="#4f7388",
            fg="white",
            font=("Arial", 12)
        ).pack(pady=10)

        # Logout button with confirmation
        logout_btn = tk.Button(
            left,
            text="Logout",
            bg="#ff4444",
            fg="white",
            font=("Arial", 16, "bold"),
            command=self.confirm_logout
        )
        logout_btn.pack(pady=20)

        # -------- RIGHT CONTENT --------
        tk.Label(
            right,
            text="Assigned Tasks",
            bg="#ffffff",
            font=("Arial", 20, "bold")
        ).pack(pady=(80, 20))

        self.tasks_text = tk.Text(right, wrap="word", height=20, font=("Arial", 12), bg="#f4f4f4", relief="flat", padx=15, pady=15)
        self.tasks_text.pack(fill="both", expand=True, padx=40, pady=20)
        self.load_tasks()

    def confirm_logout(self):
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to logout?"):
            if self.on_logout:
                self.on_logout()  # Triggers backend logout event FIRST
                
            logout_user()         # Clear local session
            self.root.destroy()

    def load_tasks(self):
        self.tasks_text.config(state="normal")
        self.tasks_text.delete("1.0", tk.END)
        self.tasks_text.insert(tk.END, "Loading assigned tasks, please wait...\n", "desc")
        self.tasks_text.config(state="disabled")

        # Fetch tasks in a background thread to prevent UI blocking
        threading.Thread(target=self._fetch_tasks_thread, daemon=True).start()

    def _fetch_tasks_thread(self):
        tasks = get_user_tasks()
        # Safely update the UI from the main thread once data is retrieved
        self.root.after(0, self._update_tasks_ui, tasks)

    def _update_tasks_ui(self, tasks):
        self.tasks_text.config(state="normal")
        self.tasks_text.delete("1.0", tk.END)

        if not tasks:
            self.tasks_text.insert(tk.END, "No tasks assigned currently.\n\nGreat job! You are all caught up.", "desc")
        else:
            pending = [t for t in tasks if str(t.get("status", "")).lower() != "completed"]
            completed = [t for t in tasks if str(t.get("status", "")).lower() == "completed"]

            if pending:
                self.tasks_text.insert(tk.END, "📌 PENDING TASKS\n\n", "header_pending")
                for idx, task in enumerate(pending, start=1):
                    title = task.get("title", "Untitled Task")
                    desc = task.get("description", "No description provided.")
                    self.tasks_text.insert(tk.END, f"{idx}. {title}\n", "title")
                    self.tasks_text.insert(tk.END, f"   {desc}\n\n", "desc")

            if completed:
                self.tasks_text.insert(tk.END, "✅ COMPLETED TASKS\n\n", "header_completed")
                for idx, task in enumerate(completed, start=1):
                    title = task.get("title", "Untitled Task")
                    desc = task.get("description", "No description provided.")
                    self.tasks_text.insert(tk.END, f"{idx}. {title}\n", "title_completed")
                    self.tasks_text.insert(tk.END, f"   {desc}\n\n", "desc_completed")

        self.tasks_text.tag_config("header_pending", font=("Arial", 14, "bold"), foreground="#d35400")
        self.tasks_text.tag_config("header_completed", font=("Arial", 14, "bold"), foreground="#27ae60")
        self.tasks_text.tag_config("title", font=("Arial", 13, "bold"), foreground="#2c3e50")
        self.tasks_text.tag_config("desc", font=("Arial", 11), foreground="#555555")
        self.tasks_text.tag_config("title_completed", font=("Arial", 13, "bold", "overstrike"), foreground="#7f8c8d")
        self.tasks_text.tag_config("desc_completed", font=("Arial", 11, "overstrike"), foreground="#95a5a6")
        self.tasks_text.config(state="disabled")
