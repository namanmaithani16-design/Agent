#!/usr/bin/env python3
"""
Test script to assign tasks to a user via the API.
This helps verify that tasks are being stored correctly in the database.

Usage:
    python test_assign_task.py --username <username> --title "<task title>" --description "<task description>"

Example:
    python test_assign_task.py --username john_intern --title "Complete Report" --description "Finish the Q1 report by EOD"
"""

import requests
import json
import argparse
import sys

# Update this to match your API server URL
API_BASE_URL = "http://localhost:5000"  # Change if running on different host/port

def assign_task(username, title, description=""):
    """Assign a task to an intern via API."""
    
    endpoint = f"{API_BASE_URL}/api/tasks/assign"
    payload = {
        "username": username,
        "title": title,
        "description": description
    }
    
    print(f"📝 Assigning task...")
    print(f"   API URL: {endpoint}")
    print(f"   Username: {username}")
    print(f"   Title: {title}")
    print(f"   Description: {description}")
    print()
    
    try:
        response = requests.post(endpoint, json=payload, timeout=10)
        response_data = response.json()
        
        if response.status_code == 201 or response_data.get("success"):
            print("✅ Task assigned successfully!")
            print(f"   Task ID: {response_data.get('task_id')}")
            print(f"   Response: {json.dumps(response_data, indent=2)}")
            return True
        else:
            print(f"❌ Failed to assign task")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {json.dumps(response_data, indent=2)}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Cannot reach {API_BASE_URL}")
        print("   Make sure your Flask server is running")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def get_tasks(username):
    """Get all tasks for a user."""
    
    endpoint = f"{API_BASE_URL}/api/tasks/{username}"
    
    print(f"📋 Fetching tasks for: {username}")
    print(f"   API URL: {endpoint}")
    print()
    
    try:
        response = requests.get(endpoint, timeout=10)
        response_data = response.json()
        
        if response.status_code == 200:
            tasks = response_data.get("tasks", [])
            print(f"✅ Found {len(tasks)} task(s)")
            for i, task in enumerate(tasks, 1):
                print(f"\n   Task {i}:")
                print(f"      ID: {task.get('id')}")
                print(f"      Title: {task.get('title')}")
                print(f"      Status: {task.get('status')}")
                print(f"      Description: {task.get('description', 'N/A')}")
            return True
        else:
            print(f"❌ Failed to fetch tasks")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {json.dumps(response_data, indent=2)}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Cannot reach {API_BASE_URL}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Assign and manage tasks via API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Assign a task
  python test_assign_task.py --username john_intern --title "Complete Report" --description "Finish by EOD"
  
  # Get all tasks for a user
  python test_assign_task.py --get-tasks john_intern
  
  # Interactive mode
  python test_assign_task.py --interactive
        """
    )
    
    parser.add_argument("--username", help="Username of the intern")
    parser.add_argument("--title", help="Task title")
    parser.add_argument("--description", default="", help="Task description")
    parser.add_argument("--get-tasks", metavar="USERNAME", help="Get all tasks for a user")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    if args.interactive:
        # Interactive mode
        print("\n🔧 Task Manager - Interactive Mode")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("  1. Assign a task")
            print("  2. Get user tasks")
            print("  3. Exit")
            
            choice = input("\nSelect option (1-3): ").strip()
            
            if choice == "1":
                username = input("Enter username: ").strip()
                title = input("Enter task title: ").strip()
                description = input("Enter task description (optional): ").strip()
                
                if username and title:
                    assign_task(username, title, description)
                else:
                    print("❌ Username and title are required")
                    
            elif choice == "2":
                username = input("Enter username: ").strip()
                if username:
                    get_tasks(username)
                else:
                    print("❌ Username is required")
                    
            elif choice == "3":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option")
                
    elif args.get_tasks:
        get_tasks(args.get_tasks)
    elif args.username and args.title:
        assign_task(args.username, args.title, args.description)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
