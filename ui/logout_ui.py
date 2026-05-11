# agent/ui/logout_ui.py

import tkinter as tk
from tkinter import messagebox
import threading
from auth.login import logout_user
from storage.db import get_user_tasks, update_task_status


class LogoutWindow:
    def __init__(self, on_logout=None):
        self.on_logout = on_logout

        self.root = tk.Tk()
        self.root.title("ISMS Logout")
        self.root.state("zoomed")  # Full screen

        # Prevent automatic logout on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.pending_checkboxes = {}  # Initialize here
        self.build_ui()
        self.root.mainloop()

    def on_close(self):
        # Destroy window immediately
        self.root.destroy()
        
        # Run cleanup in background thread
        threading.Thread(target=self._logout_cleanup, daemon=True).start()

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
        right_header_frame = tk.Frame(right, bg="#ffffff")
        right_header_frame.pack(fill="x", padx=40, pady=(80, 20))

        tk.Label(
            right_header_frame,
            text="Assigned Tasks",
            bg="#ffffff",
            font=("Arial", 20, "bold")
        ).pack(side="left")

        refresh_btn = tk.Button(
            right_header_frame,
            text="↻ Refresh",
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.load_tasks
        )
        refresh_btn.pack(side="right")

        # Create a frame for the task list with scrollbar
        task_frame = tk.Frame(right, bg="#f4f4f4")
        task_frame.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        # Canvas and scrollbar for scrolling
        self.canvas = tk.Canvas(task_frame, bg="#f4f4f4", highlightthickness=0)
        scrollbar = tk.Scrollbar(task_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f4f4f4")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mouse wheel scrolling
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.load_tasks()

    def confirm_logout(self):
        # Added Check: Verify if all tasks are complete before allowing logout
        if self.pending_checkboxes:
            msg = f"You still have {len(self.pending_checkboxes)} pending task(s).\n\nAre you sure you want to logout without completing them?"
        else:
            msg = "Are you sure you want to logout?"
            
        if messagebox.askyesno("Confirm Logout", msg):
            # Destroy window immediately for instant visual feedback
            self.root.destroy()
            
            # Run cleanup operations in background thread (non-blocking)
            threading.Thread(target=self._logout_cleanup, daemon=True).start()
    
    def _logout_cleanup(self):
        """Background cleanup to prevent UI blocking"""
        try:
            if self.on_logout:
                self.on_logout()  # Triggers backend logout event
            logout_user()  # Clear local session
        except Exception as e:
            import logging
            logging.error(f"Logout cleanup error: {e}")

    def load_tasks(self):
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Loading message
        loading_label = tk.Label(
            self.scrollable_frame,
            text="Loading assigned tasks, please wait...",
            bg="#f4f4f4",
            font=("Arial", 12),
            fg="#666666"
        )
        loading_label.pack(pady=20)

        # Fetch tasks in a background thread to prevent UI blocking
        threading.Thread(target=self._fetch_tasks_thread, daemon=True).start()

    def _fetch_tasks_thread(self):
        try:
            tasks = get_user_tasks()
            print(f"[UI] _fetch_tasks_thread received {len(tasks)} task(s): {tasks}")
            # Safely update the UI from the main thread once data is retrieved
            self.root.after(0, self._update_tasks_ui, tasks)
        except Exception as e:
            print(f"[UI] Error fetching tasks: {e}")
            self.root.after(0, self._show_error, str(e))
            
    def _show_error(self, error_msg):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        tk.Label(
            self.scrollable_frame, text=f"Error loading tasks:\n{error_msg}",
            bg="#f4f4f4", font=("Arial", 12), fg="#e74c3c"
        ).pack(pady=20)

    def _update_tasks_ui(self, tasks):
        # Clear loading message
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.complete_btn = None  # Reset button reference

        if not tasks:
            no_tasks_label = tk.Label(
                self.scrollable_frame,
                text="No tasks assigned currently.\n\nGreat job! You are all caught up.",
                bg="#f4f4f4",
                font=("Arial", 14),
                fg="#666666",
                justify="center"
            )
            no_tasks_label.pack(pady=50)
            
            # Show hint if no tasks (debug info)
            hint_label = tk.Label(
                self.scrollable_frame,
                text="💡 Tip: Use API to assign tasks\nPOST /api/tasks/assign",
                bg="#f4f4f4",
                font=("Arial", 10),
                fg="#999999",
                justify="center"
            )
            hint_label.pack(pady=10)
            return

        pending = [t for t in tasks if str(t.get("status") or t.get("taskStatus") or "pending").lower() != "completed"]
        completed = [t for t in tasks if str(t.get("status") or t.get("taskStatus") or "pending").lower() == "completed"]

        # Pending tasks section
        if pending:
            pending_header = tk.Label(
                self.scrollable_frame,
                text=f"📌 PENDING TASKS ({len(pending)})",
                bg="#f4f4f4",
                font=("Arial", 16, "bold"),
                fg="#d35400",
                anchor="w"
            )
            pending_header.pack(fill="x", padx=20, pady=(20, 10))

            self.pending_checkboxes = {}
            for task in pending:
                task_frame = tk.Frame(self.scrollable_frame, bg="#f4f4f4")
                task_frame.pack(fill="x", padx=20, pady=5)

                # Checkbox for marking complete
                var = tk.BooleanVar()
                checkbox = tk.Checkbutton(
                    task_frame,
                    variable=var,
                    bg="#f4f4f4",
                    activebackground="#f4f4f4",
                    command=lambda t=task, v=var: self._on_task_checkbox(t, v)
                )
                checkbox.pack(side="left")

                # Task content
                content_frame = tk.Frame(task_frame, bg="#f4f4f4")
                content_frame.pack(side="left", fill="x", expand=True)

                title_label = tk.Label(
                    content_frame,
                    text=task.get("title") or task.get("taskTitle") or "Untitled Task",
                    bg="#f4f4f4",
                    font=("Arial", 13, "bold"),
                    fg="#2c3e50",
                    anchor="w",
                    justify="left"
                )
                title_label.pack(fill="x")

                desc_label = tk.Label(
                    content_frame,
                    text=task.get("description") or task.get("taskDescription") or "No description provided.",
                    bg="#f4f4f4",
                    font=("Arial", 11),
                    fg="#555555",
                    anchor="w",
                    justify="left",
                    wraplength=400
                )
                desc_label.pack(fill="x")

                task_id = task.get("id") or task.get("taskId") or task.get("task_id")
                self.pending_checkboxes[task_id] = var

            # Complete selected button
            self.complete_btn = tk.Button(
                self.scrollable_frame,
                text="✓ Mark Selected as Completed",
                bg="#27ae60",
                fg="white",
                font=("Arial", 12, "bold"),
                command=self._complete_selected_tasks,
                state="disabled"
            )
            self.complete_btn.pack(pady=(10, 20))
        else:
            self.pending_checkboxes = {}

        # Completed tasks section
        if completed:
            completed_header = tk.Label(
                self.scrollable_frame,
                text=f"✅ COMPLETED TASKS ({len(completed)})",
                bg="#f4f4f4",
                font=("Arial", 16, "bold"),
                fg="#27ae60",
                anchor="w"
            )
            completed_header.pack(fill="x", padx=20, pady=(20, 10))

            for task in completed:
                task_frame = tk.Frame(self.scrollable_frame, bg="#f4f4f4")
                task_frame.pack(fill="x", padx=20, pady=5)

                # Completed checkmark
                checkmark = tk.Label(
                    task_frame,
                    text="✓",
                    bg="#f4f4f4",
                    font=("Arial", 12, "bold"),
                    fg="#27ae60"
                )
                checkmark.pack(side="left")

                # Task content (struck through)
                content_frame = tk.Frame(task_frame, bg="#f4f4f4")
                content_frame.pack(side="left", fill="x", expand=True)

                title_label = tk.Label(
                    content_frame,
                    text=task.get("title") or task.get("taskTitle") or "Untitled Task",
                    bg="#f4f4f4",
                    font=("Arial", 13, "bold", "overstrike"),
                    fg="#7f8c8d",
                    anchor="w",
                    justify="left"
                )
                title_label.pack(fill="x")

                desc_label = tk.Label(
                    content_frame,
                    text=task.get("description") or task.get("taskDescription") or "No description provided.",
                    bg="#f4f4f4",
                    font=("Arial", 11, "overstrike"),
                    fg="#95a5a6",
                    anchor="w",
                    justify="left",
                    wraplength=400
                )
                desc_label.pack(fill="x")

    def _on_task_checkbox(self, task, var):
        # Enable/disable complete button based on selections
        if self.complete_btn:
            any_selected = any(cb.get() for cb in self.pending_checkboxes.values())
            self.complete_btn.config(state="normal" if any_selected else "disabled")
        
        # Added Check: Instantly prompt and verify task completion when checkbox is ticked
        if var.get():
            task_title = task.get("title") or task.get("taskTitle") or "Untitled Task"
            if messagebox.askyesno("Complete Task", f"Do you want to mark '{task_title}' as completed right now?"):
                # Update task in background thread and instantly refresh UI
                task_id = task.get("id") or task.get("taskId") or task.get("task_id")
                threading.Thread(target=self._update_tasks_thread, args=([task_id],), daemon=True).start()
            else:
                var.set(False) # Uncheck if the user cancels
                if self.complete_btn:
                    self.complete_btn.config(state="normal" if any(cb.get() for cb in self.pending_checkboxes.values()) else "disabled")

    def _complete_selected_tasks(self):
        selected_tasks = [task_id for task_id, var in self.pending_checkboxes.items() if var.get()]
        
        if not selected_tasks:
            return

        # Confirm completion
        if not messagebox.askyesno("Confirm Completion", 
                                 f"Are you sure you want to mark {len(selected_tasks)} task(s) as completed?"):
            return

        # Update tasks in background thread
        threading.Thread(target=self._update_tasks_thread, args=(selected_tasks,), daemon=True).start()

    def _update_tasks_thread(self, task_ids):
        success_count = 0
        try:
            for task_id in task_ids:
                if update_task_status(task_id, "completed"):
                    success_count += 1
        except Exception as e:
            print(f"[UI] Error updating tasks: {e}")
            import logging
            logging.error(f"Failed to update task status: {e}")
        finally:
            # Refresh UI
            self.root.after(0, self._on_update_complete, success_count, len(task_ids))

    def _on_update_complete(self, success_count, total_count):
        if success_count == total_count:
            messagebox.showinfo("Success", f"All {success_count} task(s) marked as completed!")
        else:
            messagebox.showwarning("Partial Success", f"{success_count} out of {total_count} task(s) updated successfully.")
        
        # Reload tasks
        self.load_tasks()
