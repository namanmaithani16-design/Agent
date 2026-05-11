# Task Management Guide

## Overview
The ISMS system now includes a complete task management system that allows admins to assign tasks to interns and interns to mark them as completed.

## Features

### For Interns:
- **View Assigned Tasks**: See all pending tasks on the logout screen
- **Mark Tasks Complete**: Check off individual tasks or use "Mark Selected as Completed" button
- **View Completed Tasks**: See strikethrough list of completed tasks
- **Refresh Tasks**: Click the "↻ Refresh" button to reload tasks from the server

### For Admins:
- **Assign Tasks via API**: POST to `/api/tasks/assign` endpoint
- **Track Task Status**: GET tasks from `/api/tasks/<username>` endpoint
- **Send Notifications**: Tasks are automatically sent via email when assigned

---

## How to Assign Tasks

### Option 1: Using the Test Script (Recommended for Development)

```bash
# Navigate to project directory
cd C:\Users\naman\OneDrive\Desktop\agent

# Interactive mode
python test_assign_task.py --interactive

# Or command line
python test_assign_task.py --username john_intern --title "Complete Report" --description "Finish Q1 report"
```

### Option 2: Using cURL or Postman

```bash
curl -X POST http://localhost:5000/api/tasks/assign \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_intern",
    "title": "Complete Report",
    "description": "Finish the Q1 report by end of day"
  }'
```

### Option 3: Using Python Requests

```python
import requests

response = requests.post(
    "http://localhost:5000/api/tasks/assign",
    json={
        "username": "john_intern",
        "title": "Complete Report",
        "description": "Finish the Q1 report by EOD"
    }
)

print(response.json())
```

---

## API Endpoints

### Assign a Task (Admin)
**POST** `/api/tasks/assign`

**Request Body:**
```json
{
  "username": "john_intern",
  "title": "Task Title",
  "description": "Task Description (optional)"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Task assigned to john_intern",
  "task_id": 1,
  "task": {
    "id": 1,
    "username": "john_intern",
    "title": "Task Title",
    "description": "Task Description",
    "status": "pending",
    "created_at": "2026-05-08T10:30:00"
  }
}
```

### Get Tasks for User
**GET** `/api/tasks/<username>`

**Example:** `GET /api/tasks/john_intern`

**Response (200 OK):**
```json
{
  "username": "john_intern",
  "tasks": [
    {
      "id": 1,
      "username": "john_intern",
      "title": "Complete Report",
      "description": "Finish Q1 report",
      "status": "pending",
      "created_at": "2026-05-08T10:30:00"
    },
    {
      "id": 2,
      "username": "john_intern",
      "title": "Review Code",
      "description": "Review PR #123",
      "status": "completed",
      "created_at": "2026-05-08T09:00:00"
    }
  ]
}
```

---

## Troubleshooting

### Tasks Not Showing in UI

**Issue**: Tasks are assigned via API but don't appear on the logout screen.

**Possible Causes:**
1. **Username Mismatch**: The username used in the API call doesn't match the logged-in user's username
   - **Fix**: Ensure the username in the task assignment matches exactly what's stored in the session
   - Use `test_assign_task.py --get-tasks <username>` to verify tasks exist in database

2. **Database Connection**: The app can't connect to the database
   - **Fix**: Check DB credentials in `config.py`
   - Check logs for connection errors

3. **Session Not Initialized**: User session hasn't been properly established
   - **Fix**: Ensure user logs in correctly
   - Check session data in `auth/session.py`

**Debug Steps:**
1. Check the console output when logging in - look for:
   ```
   🔍 [TASKS] Session user object: {...}
   🔍 [TASKS] Resolved username for query: 'john_intern'
   ✅ [TASKS] Found X task(s) for username='john_intern'
   ```

2. If you see "Zero tasks matched", verify:
   - Task exists in database: `python test_assign_task.py --get-tasks john_intern`
   - Username is spelled exactly the same way
   - No extra spaces in the username

### Tasks Not Marking as Complete

**Issue**: Clicking checkbox doesn't mark task as complete

**Possible Causes:**
1. **Database Update Failed**: The update query failed silently
2. **Task ID Not Found**: The task ID is incorrect or malformed

**Debug Steps:**
1. Check the console for error messages
2. Verify the task ID exists: `python test_assign_task.py --get-tasks <username>`
3. Check database directly if needed

---

## Database Schema

### Tasks Table

```sql
CREATE TABLE tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100),           -- Must match logged-in user's username
    title VARCHAR(200),              -- Task title
    description TEXT,                -- Task description
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending' or 'completed'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## Example Workflow

### 1. Admin Assigns Task to Intern

```bash
python test_assign_task.py \
  --username john_doe \
  --title "Prepare Performance Review" \
  --description "Prepare your performance review for next week's meeting"
```

**Output:**
```
✅ Task assigned successfully!
   Task ID: 5
```

### 2. Intern Logs In

- Intern goes to login screen and enters credentials for "john_doe"
- Session is created with username="john_doe"
- Logout screen shows "Assigned Tasks" panel

### 3. Intern Sees Task

On the logout screen, the right panel displays:
```
Assigned Tasks                               ↻ Refresh

📌 PENDING TASKS (1)

☐ Prepare Performance Review
  Prepare your performance review for next week's meeting

✓ Mark Selected as Completed
```

### 4. Intern Completes Task

- Clicks the checkbox next to the task
- Confirmation dialog appears: "Do you want to mark 'Prepare Performance Review' as completed right now?"
- Clicks "Yes"
- Task moves to completed section with strikethrough
- Success message: "All 1 task(s) marked as completed!"

### 5. Verification

```bash
python test_assign_task.py --get-tasks john_doe
```

**Output:**
```
✅ Found 1 task(s)

   Task 1:
      ID: 5
      Title: Prepare Performance Review
      Status: completed
      Description: Prepare your performance review for next week's meeting
```

---

## Key Improvements Made

1. **Added Refresh Button**: Tasks panel now has a "↻ Refresh" button to manually reload tasks
2. **Fixed Button State Management**: "Mark Selected as Completed" button properly enables/disables
3. **Better Error Handling**: Code handles missing tasks gracefully
4. **Improved UI Feedback**: Users get clear confirmation when tasks are completed
5. **Debug Information**: Console logs username resolution and task fetch results

---

## Configuration

To use different API URLs or database connections, edit:
- **API URL**: In `test_assign_task.py`, change `API_BASE_URL`
- **Database**: In `config.py`, update `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`

---

## Next Steps

1. **Test task assignment**: Run `python test_assign_task.py --interactive`
2. **Verify in database**: Check if tasks are stored with the correct username
3. **Test in UI**: Log in as the user and check the logout screen
4. **Mark complete**: Test marking tasks as complete from the UI
5. **Monitor logs**: Watch console output for any errors

---

For issues or questions, check the console logs for debug messages prefixed with `[TASKS]`.
