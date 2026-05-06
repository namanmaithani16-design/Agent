# agent/ui/login_ui.py

import tkinter as tk
from tkinter import messagebox
from auth.login import login_user


class LoginWindow:

    def __init__(self, on_success=None):
        self.on_success = on_success

        self.root = tk.Tk()
        self.root.title("ISMS Login")

        # Fullscreen safely
        self.root.geometry(
            f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}"
        )
        self.root.configure(bg="white")

        self.build_ui()

        # Enter key triggers login
        self.root.bind("<Return>", lambda event: self.login_clicked())

    # ================= UI =================
    def build_ui(self):
        container = tk.Frame(self.root, bg="white")
        container.pack(fill="both", expand=True)

        left = tk.Frame(container, bg="#4f7388")
        left.pack(side="left", fill="both", expand=True)

        # right = tk.Frame(container, bg="#f2f2f2")
        # right.pack(side="right", fill="both", expand=True)

        # LEFT PANEL
        tk.Label(
            left,
            text="ISMS Login",
            bg="#4f7388",
            fg="white",
            font=("Arial", 28, "bold")
        ).pack(pady=(120, 30))

        tk.Label(left, text="Username", bg="#4f7388", fg="white",
                 font=("Arial", 12)).pack()

        self.username = tk.Entry(left, width=30, font=("Arial", 11))
        self.username.pack(pady=10)

        tk.Label(left, text="Password", bg="#4f7388", fg="white",
                 font=("Arial", 12)).pack()

        self.password = tk.Entry(left, show="*", width=30, font=("Arial", 11))
        self.password.pack(pady=10)

        self.show_password_var = tk.BooleanVar()
        show_password_check = tk.Checkbutton(
            left,
            text="Show Password",
            variable=self.show_password_var,
            command=self._toggle_password_visibility,
            bg="#4f7388",
            fg="white",
            selectcolor="#4f7388",
            activebackground="#4f7388",
            activeforeground="white",
            font=("Arial", 10)
        )
        show_password_check.pack(pady=(0, 10))

        self.login_btn = tk.Button(
            left,
            text="Login",
            bg="#2ecc71",
            fg="white",
            font=("Arial", 12, "bold"),
            width=20,
            height=2,
            command=self.login_clicked
        )
        self.login_btn.pack(pady=30)

        # RIGHT PANEL
        # tk.Label(
        #     right,
        #     text="Welcome to ISMS",
        #     bg="#f2f2f2",
        #     font=("Arial", 24)
        # ).pack(pady=(200, 20))

        # tk.Label(
        #     right,
        #     text="Employee Monitoring System",
        #     bg="#f2f2f2",
        #     font=("Arial", 12)
        # ).pack()

    def _toggle_password_visibility(self):
        """Toggles the password visibility in the entry widget."""
        if self.show_password_var.get():
            self.password.config(show="")
        else:
            self.password.config(show="*")

    # ================= LOGIN LOGIC =================
    def login_clicked(self):
        user = self.username.get().strip()
        pwd = self.password.get().strip()

        if not user or not pwd:
            messagebox.showerror("Error", "Please enter username and password")
            return

        self.login_btn.config(state="disabled")
        self.root.update_idletasks()

        try:
            success = login_user(user, pwd)
        except Exception as e:
            messagebox.showerror("Error", f"Login failed: {e}")
            self.login_btn.config(state="normal")
            return

        if success:
            self.root.destroy()

            # 🔥 IMPORTANT: Call main callback
            if self.on_success:
                self.on_success()

        else:
            messagebox.showerror("Error", "Invalid credentials")
            self.login_btn.config(state="normal")

    # ================= RUN =================
    def run(self):
        self.root.mainloop()
