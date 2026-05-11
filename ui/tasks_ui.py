# agent/ui/tasks_ui.py

import tkinter as tk
from tkinter import messagebox
import threading
from storage.db import get_user_tasks, update_task_status

class TasksWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("My Assigned Tasks")
        self.root.geometry("700x600")
        self.root.configure(bg="#ffffff")

        self.pending_checkboxes = {}
        self.build_ui()
        self.root.mainloop()

    def build_ui(self):
        top_frame = tk.Frame(self.root, bg="#ffffff")
        top_frame.pack(fill="x", padx=20, pady=(20, 10))

        header = tk.Label(
            top_frame,
            text="Assigned Tasks",
            bg="#ffffff",
            font=("Arial", 20, "bold")
        )
        header.pack(side="left")

        refresh_btn = tk.Button(
            top_frame,
            text="↻ Refresh",
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.load_tasks
        )
        refresh_btn.pack(side="right")

        task_frame = tk.Frame(self.root, bg="#f4f4f4")
        task_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.canvas = tk.Canvas(task_frame, bg="#f4f4f4", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(task_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f4f4f4")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.load_tasks()

    def load_tasks(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        loading_label = tk.Label(
            self.scrollable_frame,
            text="Loading assigned tasks, please wait...",
            bg="#f4f4f4",
            font=("Arial", 12),
            fg="#666666"
        )
        loading_label.pack(pady=20)

        threading.Thread(target=self._fetch_tasks_thread, daemon=True).start()

    def _fetch_tasks_thread(self):
        try:
            tasks = get_user_tasks()
            print(f"[UI - TASKS WINDOW] Fetched {len(tasks)} task(s): {tasks}")
            self.root.after(0, self._update_tasks_ui, tasks)
        except Exception as e:
            print(f"[UI - TASKS WINDOW] Error fetching tasks: {e}")
            self.root.after(0, self._show_error, str(e))
            
    def _show_error(self, error_msg):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        tk.Label(
            self.scrollable_frame, text=f"Error loading tasks:\n{error_msg}",
            bg="#f4f4f4", font=("Arial", 12), fg="#e74c3c"
        ).pack(pady=50)

    def _update_tasks_ui(self, tasks):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not tasks:
            tk.Label(
                self.scrollable_frame,
                text="No tasks assigned currently.\n\nGreat job! You are all caught up.",
                bg="#f4f4f4",
                font=("Arial", 14),
                fg="#666666",
                justify="center"
            ).pack(pady=50)
            return

        pending = [t for t in tasks if str(t.get("status") or t.get("taskStatus") or "pending").lower() != "completed"]
        completed = [t for t in tasks if str(t.get("status") or t.get("taskStatus") or "pending").lower() == "completed"]

        
        if pending:
            tk.Label(
                self.scrollable_frame,
                text=f"📌 PENDING TASKS ({len(pending)})",
                bg="#f4f4f4",
                font=("Arial", 16, "bold"),
                fg="#d35400",
                anchor="w"
            ).pack(fill="x", padx=20, pady=(20, 10))

            self.pending_checkboxes = {}
            for task in pending:
                task_frame = tk.Frame(self.scrollable_frame, bg="#f4f4f4")
                task_frame.pack(fill="x", padx=20, pady=5)

                var = tk.BooleanVar()
                checkbox = tk.Checkbutton(
                    task_frame,
                    variable=var,
                    bg="#f4f4f4",
                    activebackground="#f4f4f4",
                    command=lambda t=task, v=var: self._on_task_checkbox(t, v)
                )
                checkbox.pack(side="left")

                content_frame = tk.Frame(task_frame, bg="#f4f4f4")
                content_frame.pack(side="left", fill="x", expand=True)

                tk.Label(
                    content_frame,
                    text=task.get("title") or task.get("taskTitle") or "Untitled Task",
                    bg="#f4f4f4",
                    font=("Arial", 13, "bold"),
                    fg="#2c3e50",
                    anchor="w",
                    justify="left"
                ).pack(fill="x")

                tk.Label(
                    content_frame,
                    text=task.get("description") or task.get("taskDescription") or "No description provided.",
                    bg="#f4f4f4",
                    font=("Arial", 11),
                    fg="#555555",
                    anchor="w",
                    justify="left",
                    wraplength=400
                ).pack(fill="x")

                self.pending_checkboxes[task.get("id") or task.get("taskId") or task.get("task_id")] = var

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

        if completed:
            tk.Label(
                self.scrollable_frame,
                text=f"✅ COMPLETED TASKS ({len(completed)})",
                bg="#f4f4f4",
                font=("Arial", 16, "bold"),
                fg="#27ae60",
                anchor="w"
            ).pack(fill="x", padx=20, pady=(20, 10))

            for task in completed:
                task_frame = tk.Frame(self.scrollable_frame, bg="#f4f4f4")
                task_frame.pack(fill="x", padx=20, pady=5)

                tk.Label(
                    task_frame,
                    text="✓",
                    bg="#f4f4f4",
                    font=("Arial", 12, "bold"),
                    fg="#27ae60"
                ).pack(side="left")

                content_frame = tk.Frame(task_frame, bg="#f4f4f4")
                content_frame.pack(side="left", fill="x", expand=True)

                tk.Label(
                    content_frame,
                    text=task.get("title") or task.get("taskTitle") or "Untitled Task",
                    bg="#f4f4f4",
                    font=("Arial", 13, "bold", "overstrike"),
                    fg="#7f8c8d",
                    anchor="w",
                    justify="left"
                ).pack(fill="x")

                tk.Label(
                    content_frame,
                    text=task.get("description") or task.get("taskDescription") or "No description provided.",
                    bg="#f4f4f4",
                    font=("Arial", 11, "overstrike"),
                    fg="#95a5a6",
                    anchor="w",
                    justify="left",
                    wraplength=400
                ).pack(fill="x")

    def _on_task_checkbox(self, task, var):
        any_selected = any(cb.get() for cb in self.pending_checkboxes.values())
        self.complete_btn.config(state="normal" if any_selected else "disabled")

        if var.get():
            task_title = task.get("title") or task.get("taskTitle") or "Untitled Task"
            if messagebox.askyesno("Complete Task", f"Do you want to mark '{task_title}' as completed right now?"):
                threading.Thread(target=self._update_tasks_thread, args=([task.get("id") or task.get("taskId") or task.get("task_id")],), daemon=True).start()
            else:
                var.set(False)
                self.complete_btn.config(state="normal" if any(cb.get() for cb in self.pending_checkboxes.values()) else "disabled")

    def _complete_selected_tasks(self):
        selected_tasks = [task_id for task_id, var in self.pending_checkboxes.items() if var.get()]
        if not selected_tasks:
            return

        if not messagebox.askyesno("Confirm Completion", f"Are you sure you want to mark {len(selected_tasks)} task(s) as completed?"):
            return

        threading.Thread(target=self._update_tasks_thread, args=(selected_tasks,), daemon=True).start()

    def _update_tasks_thread(self, task_ids):
        try:
            for task_id in task_ids:
                update_task_status(task_id, "completed")
        except Exception as e:
            print(f"[UI - TASKS WINDOW] Error updating tasks: {e}")
        finally:
            self.root.after(0, self.load_tasks)