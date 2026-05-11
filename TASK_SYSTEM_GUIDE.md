# Task Management System - Quick Guide

## Overview
This guide explains how to use the task assignment and display system.

---

## 🚀 Quick Start

### Step 1: Run the Test Script (Easiest)
```bash
# Navigate to the agent directory
cd c:\Users\naman\OneDrive\Desktop\agent

# Activate venv
venv\Scripts\activate

# Run the test utility
python test_tasks.py
```

The script will:
1. ✅ Show your current logged-in user
2. ✅ Display all tasks in the database
3. ✅ Prompt to assign 5 demo tasks to your account
4. ✅ Display updated task list

### Step 2: Test the UI
1. Login to the application
2. Click the logout button
3. You should now see:
   - **📌 PENDING TASKS (5)** - 5 demo tasks you can complete
   - Checkboxes to select tasks
   - **✓ Mark Selected as Completed** button

---

## 🔌 Alternative: Using the API

### Assign a Task via REST API
```bash
curl -X POST http://localhost:5000/api/tasks/assign \
  -H "Content-Type: application/json" \
  -d {
    "username": "your_username",
    "title": "Review Code",
    "description": "Review pull requests"
  }
```

### Fetch Tasks for a User
```bash
curl http://localhost:5000/api/tasks/your_username
```

### Mark Task as Completed
```bash
curl -X PATCH http://localhost:5000/api/tasks/1 \
  -H "Content-Type: application/json" \
  -d {"status": "completed"}
```

---

## 🐛 Debugging: No Tasks Showing?

### Step 1: Check Session
Run the test script - it will show your current user:
```python
python test_tasks.py
```

If it says "❌ No user logged in", you need to login first.

### Step 2: Verify Tasks in Database
Check what tasks exist in the database:
```python
from storage.db import debug_all_tasks
debug_all_tasks()
```

Output example:
```
ID   Username        Title                          Status       Created
1    test_user       Review Code                    pending      2024-01-15 10:30:45
2    test_user       Complete Module A              pending      2024-01-15 10:30:45
```

### Step 3: Check Console Output
When you open the logout window, check the console for debug messages:
```
✅ [TASKS FETCH] Fetching tasks for user: test_user
✅ [TASKS FETCH] Found 5 tasks for test_user
```

If you see:
- ❌ [TASKS FETCH] No database connection → Check MySQL is running
- ❌ [TASKS FETCH] No user in session → Login first
- ✅ [TASKS FETCH] Found 0 tasks → No tasks assigned (run test_tasks.py to add them)

---

## 📋 Task System Features

### ✅ For Users (Interns)
1. **View Assigned Tasks** - See all pending tasks in logout window
2. **Select Tasks** - Checkbox each task you've completed
3. **Mark Complete** - Click "✓ Mark Selected as Completed"
4. **View History** - See completed tasks with strikethrough
5. **Instant Logout** - Window closes immediately, cleanup happens in background

### 👨‍💼 For Admin
1. **Assign Tasks** - Use API endpoint `/api/tasks/assign`
2. **View All Tasks** - Use `/api/tasks` endpoint
3. **Track Status** - Monitor pending vs completed tasks
4. **See Statistics** - Use `/api/tasks/stats/summary` for overview

---

## 🗂️ Database Schema

```sql
CREATE TABLE tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📝 Sample Task Data

When you run `python test_tasks.py`, these 5 tasks are created:
1. **Review Code** - Review pull requests for feature X
2. **Complete Module A** - Finish implementing authentication module
3. **Write Unit Tests** - Write comprehensive unit tests for API endpoints
4. **Update Documentation** - Update API documentation with new endpoints
5. **Database Optimization** - Optimize database queries for performance

---

## 🔧 Manual Task Insertion (Advanced)

If you want to add tasks manually:

```python
from storage.db import get_connection
from datetime import datetime

conn = get_connection()
cur = conn.cursor()

cur.execute(
    """INSERT INTO tasks (username, title, description, status, created_at)
       VALUES (%s, %s, %s, %s, %s)""",
    ("your_username", "Task Title", "Task Description", "pending", datetime.now())
)
conn.commit()
cur.close()
conn.close()

print("✅ Task added!")
```

---

## 🎯 Workflow Example

1. **Admin** assigns task via API:
   ```
   POST /api/tasks/assign
   {"username": "intern1", "title": "Setup Database", "description": "..."}
   ```

2. **Intern** logs in and navigates to logout

3. **Logout Window** shows:
   ```
   📌 PENDING TASKS (1)
   ☐ Setup Database
      Setup Database connection and migration
   
   ✓ Mark Selected as Completed
   ```

4. **Intern** checks the checkbox and clicks "✓ Mark Selected as Completed"

5. **Admin** verifies task is marked complete via API:
   ```
   GET /api/tasks/intern1
   // Returns status: "completed"
   ```

6. **Admin dashboard** reflects the completed task

---

## ⚡ Performance Notes

- ✅ Task fetch runs in background thread (non-blocking)
- ✅ Logout window closes instantly (UI responsive)
- ✅ Database cleanup happens in background
- ✅ No UI freezing during database operations
- ✅ Smooth task rendering with Tkinter Canvas

---

## 📚 Related Files

- `storage/db.py` - Database functions (get_user_tasks, update_task_status)
- `ui/logout_ui.py` - Task display UI (LogoutWindow class)
- `routes/task_routes.py` - REST API endpoints
- `test_tasks.py` - Testing utility script

---

## 🆘 Still Having Issues?

1. **Check MySQL is running** on `93.127.199.4:3306`
2. **Verify credentials** in `config.py`
3. **Check venv is activated** before running
4. **Review console output** for error messages
5. **Run test_tasks.py** to verify connectivity

For more details, see the full API documentation in `TASK_MANAGEMENT.md`.
