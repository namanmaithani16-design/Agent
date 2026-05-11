# agent/routes/task_routes.py

from flask import Blueprint, request, jsonify
import mysql.connector
from datetime import datetime
from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

task_bp = Blueprint("task_bp", __name__)


def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )


# ==============================
# ASSIGN TASK TO INTERN (ADMIN)
# ==============================

@task_bp.route("/api/tasks/assign", methods=["POST"])
def assign_task():
    conn = None
    cursor = None
    try:
        data = request.get_json() or {}

        username = (data.get("username") or "").strip()
        title = (data.get("title") or "").strip()
        description = data.get("description")

        if not username or not title:
            return jsonify({"error": "Username and title are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Use userId instead of username (column doesn't exist)
        cursor.execute("""
            INSERT INTO tasks (userId, title, description, status, createdAt)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            username,
            title,
            (description or "").strip(),
            "pending",
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))

        conn.commit()
        task_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": f"Task assigned to {username}",
            "task_id": task_id,
            "task": {
                "id": task_id,
                "userId": username,
                "title": title,
                "description": (description or "").strip(),
                "status": "pending",
                "createdAt": datetime.now().isoformat()
            }
        }), 201

    except Exception as e:
        return jsonify({"error": f"Failed to assign task: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==============================
# GET ALL TASKS FOR INTERN
# ==============================

@task_bp.route("/api/tasks/<username>", methods=["GET"])
def get_intern_tasks(username):
    conn = None
    cursor = None
    try:
        username = (username or "").strip()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Use userId and email instead of username
        cursor.execute("""
            SELECT id, userId, title, description, status, createdAt,
                   deadline, priority, assignedBy, assignedTo, email, domain
            FROM tasks
            WHERE LOWER(TRIM(userId)) = LOWER(TRIM(%s))
               OR LOWER(TRIM(assignedTo)) = LOWER(TRIM(%s))
            ORDER BY id DESC
        """, (username, username))

        tasks = cursor.fetchall()

        # Convert datetime objects to strings
        for task in tasks:
            if isinstance(task.get("createdAt"), datetime):
                task["createdAt"] = task["createdAt"].isoformat()
            if task.get("deadline"):
                task["deadline"] = str(task["deadline"])

        pending_count = len([t for t in tasks if str(t.get("status", "")).lower() != "completed"])
        completed_count = len(tasks) - pending_count

        return jsonify({
            "success": True,
            "username": username,
            "total_tasks": len(tasks),
            "pending_tasks": pending_count,
            "completed_tasks": completed_count,
            "tasks": tasks
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch tasks: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==============================
# GET ALL TASKS (ADMIN DASHBOARD)
# ==============================

@task_bp.route("/api/tasks", methods=["GET"])
def get_all_tasks():
    conn = None
    cursor = None
    try:
        status_filter = request.args.get("status", "").lower()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if status_filter and status_filter in ["pending", "completed"]:
            cursor.execute("""
                SELECT id, userId, title, description, status, createdAt,
                       deadline, priority, assignedBy, assignedTo, email, domain
                FROM tasks
                WHERE LOWER(status) = %s
                ORDER BY id DESC
            """, (status_filter,))
        else:
            cursor.execute("""
                SELECT id, userId, title, description, status, createdAt,
                       deadline, priority, assignedBy, assignedTo, email, domain
                FROM tasks
                ORDER BY id DESC
            """)

        tasks = cursor.fetchall()

        # Convert datetime objects to strings
        for task in tasks:
            if isinstance(task.get("createdAt"), datetime):
                task["createdAt"] = task["createdAt"].isoformat()
            if task.get("deadline"):
                task["deadline"] = str(task["deadline"])

        pending_count = len([t for t in tasks if str(t.get("status", "")).lower() != "completed"])
        completed_count = len(tasks) - pending_count

        return jsonify({
            "success": True,
            "total_tasks": len(tasks),
            "pending_tasks": pending_count,
            "completed_tasks": completed_count,
            "tasks": tasks
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch tasks: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==============================
# UPDATE TASK STATUS
# ==============================

@task_bp.route("/api/tasks/<int:task_id>", methods=["PATCH"])
def update_task(task_id):
    conn = None
    cursor = None
    try:
        data = request.get_json() or {}
        status = data.get("status", "").lower()

        if not status or status not in ["pending", "completed"]:
            return jsonify({"error": "Status must be 'pending' or 'completed'"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "UPDATE tasks SET status = %s WHERE id = %s",
            (status, task_id)
        )

        if cursor.rowcount == 0:
            return jsonify({"error": f"Task {task_id} not found"}), 404

        conn.commit()

        # Fetch updated task
        cursor.execute("""
            SELECT id, userId, title, description, status, createdAt,
                   deadline, priority, assignedBy, assignedTo, email, domain
            FROM tasks WHERE id = %s
        """, (task_id,))

        updated_task = cursor.fetchone()

        if updated_task and isinstance(updated_task.get("createdAt"), datetime):
            updated_task["createdAt"] = updated_task["createdAt"].isoformat()

        return jsonify({
            "success": True,
            "message": f"Task {task_id} status updated to '{status}'",
            "task": updated_task
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to update task: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==============================
# GET TASK STATISTICS
# ==============================

@task_bp.route("/api/tasks/stats/summary", methods=["GET"])
def get_task_stats():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Overall stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_tasks,
                SUM(CASE WHEN LOWER(status) = 'pending' THEN 1 ELSE 0 END) as pending_tasks,
                SUM(CASE WHEN LOWER(status) = 'completed' THEN 1 ELSE 0 END) as completed_tasks
            FROM tasks
        """)
        overall_stats = cursor.fetchone()

        # Per-intern stats using userId instead of username
        cursor.execute("""
            SELECT
                userId,
                assignedTo,
                email,
                COUNT(*) as total_tasks,
                SUM(CASE WHEN LOWER(status) = 'pending' THEN 1 ELSE 0 END) as pending_tasks,
                SUM(CASE WHEN LOWER(status) = 'completed' THEN 1 ELSE 0 END) as completed_tasks
            FROM tasks
            GROUP BY userId, assignedTo, email
            ORDER BY userId
        """)
        intern_stats = cursor.fetchall()

        return jsonify({
            "success": True,
            "overall": {
                "total_tasks": overall_stats["total_tasks"] or 0,
                "pending_tasks": overall_stats["pending_tasks"] or 0,
                "completed_tasks": overall_stats["completed_tasks"] or 0
            },
            "by_intern": intern_stats
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch statistics: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()