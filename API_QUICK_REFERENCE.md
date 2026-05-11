# Task Management API - Quick Reference

## Base URL
```
http://your-api-server:port
```

## Authentication
Currently no authentication required. Add your own security layer as needed.

---

## 📋 Endpoints Quick Reference

### 1️⃣ Assign Task to Intern

**Endpoint:** `POST /api/tasks/assign`

**Request:**
```bash
curl -X POST http://localhost:5000/api/tasks/assign \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_intern",
    "title": "Complete Module A",
    "description": "Finish implementing the authentication module"
  }'
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
    "title": "Complete Module A",
    "description": "Finish implementing the authentication module",
    "status": "pending",
    "created_at": "2026-05-07T17:35:00"
  }
}
```

---

### 2️⃣ Get Tasks for Specific Intern

**Endpoint:** `GET /api/tasks/{username}`

**Request:**
```bash
curl http://localhost:5000/api/tasks/john_intern
```

**Response (200 OK):**
```json
{
  "success": true,
  "username": "john_intern",
  "total_tasks": 3,
  "pending_tasks": 1,
  "completed_tasks": 2,
  "tasks": [
    {
      "id": 1,
      "username": "john_intern",
      "title": "Complete Module A",
      "description": "Finish implementing...",
      "status": "completed",
      "created_at": "2026-05-07T10:00:00"
    },
    {
      "id": 2,
      "username": "john_intern",
      "title": "Code Review",
      "description": "Review PR #123",
      "status": "completed",
      "created_at": "2026-05-07T11:00:00"
    },
    {
      "id": 3,
      "username": "john_intern",
      "title": "Documentation",
      "description": "Write API docs",
      "status": "pending",
      "created_at": "2026-05-07T14:00:00"
    }
  ]
}
```

---

### 3️⃣ Get All Tasks (Admin View)

**Endpoint:** `GET /api/tasks`

**Parameters:**
- `status` (optional): `pending` or `completed`

**Requests:**
```bash
# Get all tasks
curl http://localhost:5000/api/tasks

# Get only pending tasks
curl http://localhost:5000/api/tasks?status=pending

# Get only completed tasks
curl http://localhost:5000/api/tasks?status=completed
```

**Response (200 OK):**
```json
{
  "success": true,
  "total_tasks": 5,
  "pending_tasks": 2,
  "completed_tasks": 3,
  "tasks": [
    {
      "id": 1,
      "username": "john_intern",
      "title": "Complete Module A",
      "description": "...",
      "status": "completed",
      "created_at": "2026-05-07T10:00:00"
    },
    {
      "id": 3,
      "username": "john_intern",
      "title": "Documentation",
      "description": "...",
      "status": "pending",
      "created_at": "2026-05-07T14:00:00"
    },
    {
      "id": 4,
      "username": "jane_intern",
      "title": "Testing",
      "description": "...",
      "status": "pending",
      "created_at": "2026-05-07T15:00:00"
    }
  ]
}
```

---

### 4️⃣ Update Task Status

**Endpoint:** `PATCH /api/tasks/{task_id}`

**Request:**
```bash
curl -X PATCH http://localhost:5000/api/tasks/3 \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Task 3 status updated to 'completed'",
  "task": {
    "id": 3,
    "username": "john_intern",
    "title": "Documentation",
    "description": "Write API docs",
    "status": "completed",
    "created_at": "2026-05-07T14:00:00"
  }
}
```

**Response (404 Not Found):**
```json
{
  "error": "Task 999 not found"
}
```

---

### 5️⃣ Get Task Statistics

**Endpoint:** `GET /api/tasks/stats/summary`

**Request:**
```bash
curl http://localhost:5000/api/tasks/stats/summary
```

**Response (200 OK):**
```json
{
  "success": true,
  "overall": {
    "total_tasks": 10,
    "pending_tasks": 4,
    "completed_tasks": 6
  },
  "by_intern": [
    {
      "username": "jane_intern",
      "total_tasks": 3,
      "pending_tasks": 1,
      "completed_tasks": 2
    },
    {
      "username": "john_intern",
      "total_tasks": 4,
      "pending_tasks": 2,
      "completed_tasks": 2
    },
    {
      "username": "mike_intern",
      "total_tasks": 3,
      "pending_tasks": 1,
      "completed_tasks": 2
    }
  ]
}
```

---

## 🔍 Common Use Cases

### Use Case 1: Assign Multiple Tasks to an Intern

```bash
# Task 1
curl -X POST http://localhost:5000/api/tasks/assign \
  -H "Content-Type: application/json" \
  -d '{"username":"intern1","title":"API Development","description":"Build REST API"}'

# Task 2
curl -X POST http://localhost:5000/api/tasks/assign \
  -H "Content-Type: application/json" \
  -d '{"username":"intern1","title":"Unit Tests","description":"Write unit tests for API"}'

# Task 3
curl -X POST http://localhost:5000/api/tasks/assign \
  -H "Content-Type: application/json" \
  -d '{"username":"intern1","title":"Documentation","description":"Document the API endpoints"}'
```

### Use Case 2: Monitor Intern Progress

```bash
# Get all tasks
curl http://localhost:5000/api/tasks/intern1

# Get only pending tasks
curl http://localhost:5000/api/tasks/intern1?status=pending

# Get statistics
curl http://localhost:5000/api/tasks/stats/summary
```

### Use Case 3: Update Task Status via Admin

```bash
# Mark task as complete (if intern couldn't mark it)
curl -X PATCH http://localhost:5000/api/tasks/5 \
  -H "Content-Type: application/json" \
  -d '{"status":"completed"}'
```

### Use Case 4: Create Admin Dashboard

```bash
# 1. Get overall stats
curl http://localhost:5000/api/tasks/stats/summary

# 2. Get all pending tasks
curl http://localhost:5000/api/tasks?status=pending

# 3. Loop through interns and get their individual stats
for intern in john jane mike; do
  echo "=== $intern ==="
  curl http://localhost:5000/api/tasks/$intern
done
```

---

## ⚠️ Error Responses

### 400 Bad Request
```json
{
  "error": "Username and title are required"
}
```

### 404 Not Found
```json
{
  "error": "Task 999 not found"
}
```

### 500 Server Error
```json
{
  "error": "Failed to assign task: Database connection failed"
}
```

---

## 🚀 Integration Example (Python)

```python
import requests
import json

BASE_URL = "http://localhost:5000"

# Assign task
def assign_task(username, title, description=""):
    response = requests.post(
        f"{BASE_URL}/api/tasks/assign",
        json={
            "username": username,
            "title": title,
            "description": description
        }
    )
    return response.json()

# Get intern tasks
def get_intern_tasks(username):
    response = requests.get(f"{BASE_URL}/api/tasks/{username}")
    return response.json()

# Get all tasks
def get_all_tasks(status=None):
    url = f"{BASE_URL}/api/tasks"
    params = {"status": status} if status else {}
    response = requests.get(url, params=params)
    return response.json()

# Update task
def update_task(task_id, status):
    response = requests.patch(
        f"{BASE_URL}/api/tasks/{task_id}",
        json={"status": status}
    )
    return response.json()

# Get stats
def get_stats():
    response = requests.get(f"{BASE_URL}/api/tasks/stats/summary")
    return response.json()

# Usage
if __name__ == "__main__":
    # Assign task
    result = assign_task("john_intern", "Build Login Form", "Create responsive login page")
    print("Assigned:", result)
    
    # Get tasks
    tasks = get_intern_tasks("john_intern")
    print("John's tasks:", tasks)
    
    # Get stats
    stats = get_stats()
    print("Overall stats:", stats)
```

---

## 🧪 Testing with Postman

1. **Create Environment Variable:**
   - `base_url` = `http://localhost:5000`

2. **Create Collection with these requests:**

   **POST Assign Task**
   - URL: `{{base_url}}/api/tasks/assign`
   - Body (JSON):
     ```json
     {
       "username": "john_intern",
       "title": "Test Task",
       "description": "Testing the API"
     }
     ```

   **GET Tasks**
   - URL: `{{base_url}}/api/tasks`

   **GET Intern Tasks**
   - URL: `{{base_url}}/api/tasks/john_intern`

   **PATCH Update**
   - URL: `{{base_url}}/api/tasks/1`
   - Body (JSON):
     ```json
     {
       "status": "completed"
     }
     ```

   **GET Stats**
   - URL: `{{base_url}}/api/tasks/stats/summary`

---

## 📊 Response Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success (GET, PATCH) | Task fetched/updated |
| 201 | Created (POST) | Task assigned |
| 400 | Bad Request | Missing required field |
| 404 | Not Found | Task doesn't exist |
| 500 | Server Error | Database error |

---

## 💡 Tips

- Always include `Content-Type: application/json` header for POST/PATCH requests
- Task status is case-insensitive in filters but stored as-is
- Pagination not yet implemented - consider adding for large task lists
- All timestamps are in ISO 8601 format
- Use `status=pending` to get incomplete tasks for dashboard
- Use `status=completed` to track completed work
