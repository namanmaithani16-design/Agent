# agent/ui/logout_ui.py

import tkinter as tk
from auth.login import logout_user


class LogoutWindow:
    def __init__(self, on_logout=None):
        self.on_logout = on_logout

        self.root = tk.Tk()
        self.root.title("ISMS Logout")
        self.root.state("zoomed")  # Full screen

        self.build_ui()
        self.root.mainloop()

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
            font=("Arial", 11)
        ).pack(pady=5)

        tk.Button(
            left,
            text="Logout",
            bg="#2ecc71",
            fg="white",
            width=20,
            height=2,
            font=("Arial", 11, "bold"),
            command=self.confirm_logout
        ).pack(pady=30)

        # -------- RIGHT CONTENT --------
        tk.Label(
            right,
            text="Welcome to ISMS",
            bg="#ffffff",
            fg="black",
            font=("Arial", 24)
        ).pack(pady=(120, 20))

        tk.Label(
            right,
            text="Employee Monitoring System",
            bg="#ffffff",
            fg="black",
            font=("Arial", 11)
        ).pack()

    def confirm_logout(self):
        try:
            # 🔹 Stop session & monitoring
            logout_user()

            # 🔹 If callback exists (main.py logic)
            if self.on_logout:
                self.on_logout()

        except Exception as e:
            print("Logout error:", e)

        finally:
            self.root.destroy()
