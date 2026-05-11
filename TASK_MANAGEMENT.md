# Task Management System Documentation

## Overview

This task management system allows admins to assign tasks to interns. Interns can view their assigned tasks in the logout window, mark them as completed, and admins can track completion status through the API.

## Database Schema

The `tasks` table structure:
```sql
CREATE TABLE tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100),
    title VARCHAR(200),
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

## Features

### 1. **Intern-Facing Features** (Logout Window)
- View all assigned pending tasks
- View completed tasks (struck through)
- Check off tasks to mark as completed
- Click "Mark Selected as Completed" button
- Real-time synchronization with database

### 2. **Admin API Endpoints**

#### Assign Task to Intern
```
POST /api/tasks/assign
Content-Type: application/json

{
    "username": "intern_username",
    "title": "Task Title",
    "description": "Detailed task description (optional)"
}

Response (201):
{
    "success": true,
    "message": "Task assigned to intern_username",
    "task_id": 1,
    "task": {
        "id": 1,
        "username": "intern_username",
        "title": "Task Title",
        "description": "Detailed task description",
        "status": "pending",
        "created_at": "2026-05-07T17:37:00"
    }
}
```

#### Get All Tasks for a Specific Intern
```
GET /api/tasks/<username>

Response (200):
{
    "success": true,
    "username": "intern_username",
    "total_tasks": 5,
    "pending_tasks": 3,
    "completed_tasks": 2,
    "tasks": [
        {
            "id": 1,
            "username": "intern_username",
            "title": "Task 1",
            "description": "Description",
            "status": "completed",
            "created_at": "2026-05-07T17:30:00"
        },
        ...
    ]
}
```

#### Get All Tasks (Admin Dashboard)
```
GET /api/tasks
GET /api/tasks?status=pending
GET /api/tasks?status=completed

Response (200):
{
    "success": true,
    "total_tasks": 15,
    "pending_tasks": 8,
    "completed_tasks": 7,
    "tasks": [
        {
            "id": 1,
            "username": "intern1",
            "title": "Task 1",
            "status": "completed",
            "created_at": "2026-05-07T17:30:00"
        },
        ...
    ]
}
```

#### Update Task Status
```
PATCH /api/tasks/<task_id>
Content-Type: application/json

{
    "status": "completed"  // or "pending"
}

Response (200):
{
    "success": true,
    "message": "Task 1 status updated to 'completed'",
    "task": {
        "id": 1,
        "username": "intern_username",
        "title": "Task Title",
        "status": "completed"
    }
}
```

#### Get Task Statistics
```
GET /api/tasks/stats/summary

Response (200):
{
    "success": true,
    "overall": {
        "total_tasks": 15,
        "pending_tasks": 8,
        "completed_tasks": 7
    },
    "by_intern": [
        {
            "username": "intern1",
            "total_tasks": 5,
            "pending_tasks": 2,
            "completed_tasks": 3
        },
        {
            "username": "intern2",
            "total_tasks": 10,
            "pending_tasks": 6,
            "completed_tasks": 4
        }
    ]
}
```

## Workflow

### For Admins:
1. Assign task to intern via API: `POST /api/tasks/assign`
2. View all tasks: `GET /api/tasks`
3. Track completion status: `GET /api/tasks/stats/summary`
4. View specific intern's tasks: `GET /api/tasks/<username>`

### For Interns:
1. Login to the application
2. At logout time, view assigned tasks in logout window
3. Check off completed tasks
4. Click "Mark Selected as Completed"
5. Confirmation message shows success
6. Logout and proceed

## Integration

To integrate the task routes with your Flask app, add this to your main Flask app file:

```python
from routes.task_routes import task_bp

# Register blueprint
app.register_blueprint(task_bp)
```

## Database Updates

The database is automatically initialized with the tasks table when the application starts. If the table doesn't exist, it will be created during `init_db()`.

## Status Values
- `pending` - Task has not been completed
- `completed` - Task has been marked as completed by intern

## Error Handling

All endpoints return appropriate HTTP status codes:
- 200: Success
- 201: Created (task assigned)
- 400: Bad request (missing/invalid parameters)
- 404: Not found (task doesn't exist)
- 500: Server error

## Example Usage

### 1. Assign multiple tasks to an intern
```bash
curl -X POST http://your-api:5000/api/tasks/assign \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_intern",
    "title": "Complete Project A",
    "description": "Finish the front-end components"
  }'

curl -X POST http://your-api:5000/api/tasks/assign \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_intern",
    "title": "Code Review",
    "description": "Review pull requests for feature X"
  }'
```

### 2. Check intern's tasks
```bash
curl http://your-api:5000/api/tasks/john_intern
```

### 3. View all pending tasks
```bash
curl http://your-api:5000/api/tasks?status=pending
```

### 4. Get dashboard statistics
```bash
curl http://your-api:5000/api/tasks/stats/summary
```

## Next Steps

1. Register the task blueprint in your Flask application
2. Test the endpoints using the examples above
3. Build an admin dashboard UI to consume these APIs
4. Monitor task completion rates and intern productivity
