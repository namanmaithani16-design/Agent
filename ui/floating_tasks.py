# agent/ui/floating_tasks.py

import tkinter as tk
from tkinter import messagebox
import threading
from storage.db import get_user_tasks, update_task_status

class FloatingTaskWidget:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("My Tasks")
        
        # Make window float always on top, remove standard window borders
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        
        # Position in top right corner of the screen
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"250x300+{screen_width - 270}+50")
        self.root.configure(bg="#fdfd96")  # Sticky note yellow
        
        self.build_ui()
        self.root.mainloop()
        
    def build_ui(self):
        # Header Frame
        header_frame = tk.Frame(self.root, bg="#f39c12")
        header_frame.pack(fill="x")
        
        tk.Label(
            header_frame, 
            text="📌 Pending Tasks", 
            bg="#f39c12", fg="white", 
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=5, pady=5)
        
        # Close button to hide the widget
        tk.Button(
            header_frame, 
            text="X", bg="#f39c12", fg="white", bd=0, 
            command=self.root.destroy
        ).pack(side="right", padx=5)
        
        # Task list frame
        self.list_frame = tk.Frame(self.root, bg="#fdfd96")
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Refresh button at bottom
        tk.Button(
            self.root, text="↻ Refresh", 
            bg="#fdfd96", bd=1, command=self.load_tasks
        ).pack(pady=5)

        self.load_tasks()
        
    def load_tasks(self):
        # Run fetch in background thread so it doesn't freeze the screen
        threading.Thread(target=self._fetch_tasks, daemon=True).start()
        
    def _fetch_tasks(self):
        try:
            tasks = get_user_tasks()
            self.root.after(0, self._update_ui, tasks)
        except Exception as e:
            print(f"[UI - FLOATING] Error fetching tasks: {e}")
            self.root.after(0, self._show_error, str(e))
            
    def _show_error(self, error_msg):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        tk.Label(self.list_frame, text="Error loading tasks", bg="#fdfd96", fg="red", font=("Arial", 9, "bold")).pack(pady=20)
        
    def _update_ui(self, tasks):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
            
        pending = [t for t in tasks if str(t.get("status") or "pending").lower() != "completed"]
        
        if not pending:
            tk.Label(self.list_frame, text="No pending tasks!\nYou're all caught up.", bg="#fdfd96", font=("Arial", 9, "italic")).pack(pady=20)
            return
            
        for task in pending[:5]:  # Show top 5
            task_frame = tk.Frame(self.list_frame, bg="#fdfd96")
            task_frame.pack(fill="x", pady=4)
            
            var = tk.BooleanVar()
            cb = tk.Checkbutton(
                task_frame, 
                variable=var, 
                bg="#fdfd96", 
                activebackground="#fdfd96",
                command=lambda t=task, v=var: self._on_task_check(t, v)
            )
            cb.pack(side="left")
            
            title = task.get("title") or task.get("taskTitle") or "Untitled"
            tk.Label(task_frame, text=title, bg="#fdfd96", font=("Arial", 10), anchor="w", justify="left", wraplength=190).pack(side="left", fill="x")
            
        if len(pending) > 5:
            tk.Label(self.list_frame, text=f"...and {len(pending)-5} more", bg="#fdfd96", font=("Arial", 8, "italic")).pack(pady=5)
            
    def _on_task_check(self, task, var):
        if var.get():
            title = task.get("title") or task.get("taskTitle") or "Untitled"
            if messagebox.askyesno("Complete Task", f"Mark '{title}' as completed?"):
                task_id = task.get("id") or task.get("taskId") or task.get("task_id")
                threading.Thread(target=self._update_task_thread, args=(task_id,), daemon=True).start()
            else:
                var.set(False)
                
    def _update_task_thread(self, task_id):
        try:
            update_task_status(task_id, "completed")
        except Exception as e:
            print(f"[UI - FLOATING] Error updating task: {e}")
        finally:
            self.root.after(0, self.load_tasks)