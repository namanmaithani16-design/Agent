"""
TASK SYSTEM DIAGNOSTICS
Helps identify why tasks aren't showing after assignment
"""

import sys
sys.path.insert(0, r'c:\Users\naman\OneDrive\Desktop\agent')

from storage.db import get_connection, debug_all_tasks, debug_current_user, get_user_tasks
from auth.session import get_current_user
import mysql.connector

def separator(title=""):
    if title:
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}")
    else:
        print(f"\n{'-'*70}\n")

def check_db_connection():
    """Test MySQL connection"""
    separator("1️⃣  DATABASE CONNECTION TEST")
    try:
        conn = get_connection()
        if conn:
            print("✅ MySQL connection: SUCCESS")
            print(f"   Server: Connected")
            
            # Check if tasks table exists
            cur = conn.cursor()
            cur.execute("SHOW TABLES LIKE 'tasks'")
            if cur.fetchone():
                print("✅ Tasks table: EXISTS")
                
                # Count total tasks
                cur.execute("SELECT COUNT(*) as count FROM tasks")
                count = cur.fetchone()[0]
                print(f"   Total tasks in database: {count}")
            else:
                print("❌ Tasks table: NOT FOUND")
            
            cur.close()
            conn.close()
            return True
        else:
            print("❌ MySQL connection: FAILED")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def check_session():
    """Check if user is logged in"""
    separator("2️⃣  SESSION & LOGIN TEST")
    print("Checking current session...")
    debug_current_user()
    
    current_user = get_current_user()
    if current_user:
        print(f"✅ Session status: LOGGED IN")
        return current_user.get("username")
    else:
        print("❌ Session status: NOT LOGGED IN")
        print("\n⚠️  You must be logged in to test tasks!")
        print("   Login to the application first, then run this script.")
        return None

def check_tasks_in_db(username):
    """Check tasks for specific user in database"""
    separator("3️⃣  TASKS IN DATABASE")
    
    conn = get_connection()
    if not conn:
        print("❌ Cannot connect to database")
        return 0
    
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        
        # Check all tasks
        print("📊 ALL TASKS IN DATABASE:")
        cur.execute("SELECT id, username, title, status FROM tasks ORDER BY username, created_at DESC")
        all_tasks = cur.fetchall()
        
        if not all_tasks:
            print("   (none)")
        else:
            print(f"   {'ID':<4} {'Username':<15} {'Title':<35} {'Status':<10}")
            print(f"   {'-'*64}")
            for task in all_tasks:
                user = task['username']
                title = str(task['title'])[:33]
                status = task['status']
                print(f"   {task['id']:<4} {user:<15} {title:<35} {status:<10}")
        
        # Check tasks for current user
        separator()
        print(f"📌 TASKS FOR USER '{username}':")
        cur.execute(
            "SELECT id, username, title, status, created_at FROM tasks WHERE username=%s ORDER BY created_at DESC",
            (username,)
        )
        user_tasks = cur.fetchall()
        
        if not user_tasks:
            print(f"   ❌ NO TASKS found for user '{username}'")
            print(f"\n   This is the problem! Tasks table might have:")
            print(f"   - Different username (check capitalization)")
            print(f"   - Tasks assigned to different user")
        else:
            print(f"   ✅ Found {len(user_tasks)} tasks:\n")
            print(f"   {'ID':<4} {'Title':<35} {'Status':<12} {'Created':<19}")
            print(f"   {'-'*70}")
            for task in user_tasks:
                title = str(task['title'])[:33]
                print(f"   {task['id']:<4} {title:<35} {task['status']:<12} {str(task['created_at']):<19}")
        
        return len(user_tasks)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0
    finally:
        if cur: cur.close()
        if conn: conn.close()

def check_task_fetch():
    """Test actual get_user_tasks() function"""
    separator("4️⃣  TASK FETCH FUNCTION TEST")
    
    print("Calling get_user_tasks()...\n")
    tasks = get_user_tasks()
    
    if tasks:
        print(f"✅ get_user_tasks() returned {len(tasks)} tasks")
        for i, task in enumerate(tasks, 1):
            print(f"\n   Task {i}:")
            print(f"   - ID: {task.get('id')}")
            print(f"   - Title: {task.get('title')}")
            print(f"   - Description: {task.get('description')}")
            print(f"   - Status: {task.get('status')}")
    else:
        print("❌ get_user_tasks() returned EMPTY")
        print("\n   Possible causes:")
        print("   1. Tasks not assigned to this user")
        print("   2. Username mismatch in database")
        print("   3. Session user doesn't match assigned user")

def check_username_case():
    """Check if username case matters"""
    separator("5️⃣  USERNAME CASE SENSITIVITY CHECK")
    
    current_user = get_current_user()
    if not current_user:
        print("No user logged in")
        return
    
    username = current_user.get("username")
    print(f"Your username in session: '{username}'")
    print(f"Character count: {len(username)}")
    print(f"Bytes: {username.encode()}")
    
    # Check database for similar usernames
    conn = get_connection()
    if conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT DISTINCT username FROM tasks ORDER BY username")
        usernames = cur.fetchall()
        
        if usernames:
            print(f"\n✅ Usernames in tasks table:")
            for row in usernames:
                db_username = row['username']
                match = "✓ MATCH" if db_username == username else "✗ Different"
                print(f"   - '{db_username}' {match}")
        else:
            print("\n❌ No usernames found in tasks table")
        
        cur.close()
        conn.close()

def main():
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  🔍 TASK SYSTEM DIAGNOSTICS".center(68) + "║")
    print("║" + "  Identify why tasks aren't showing".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    # Run all diagnostics
    if not check_db_connection():
        print("\n⚠️  FIX NEEDED: MySQL server is not accessible")
        return
    
    username = check_session()
    if not username:
        print("\n⚠️  FIX NEEDED: Login to the application first")
        return
    
    task_count = check_tasks_in_db(username)
    check_task_fetch()
    check_username_case()
    
    # Summary
    separator("DIAGNOSIS SUMMARY")
    
    if task_count > 0:
        print("✅ Tasks ARE in database for your user")
        print("✅ Database function should be working")
        print("\n❓ If tasks still don't show in UI:")
        print("   1. Try logging OUT and back IN (refresh session)")
        print("   2. Close and restart the application completely")
        print("   3. The logout window should then show your tasks")
    else:
        print("❌ NO TASKS found for your username")
        print("\n📝 To fix this:")
        print("   Option A: Run test_tasks.py to assign demo tasks")
        print("   Option B: Use API endpoint to assign tasks manually:")
        print("\n      curl -X POST http://localhost:5000/api/tasks/assign \\")
        print('             -H "Content-Type: application/json" \\')
        print(f'             -d "{{\\"username\\": \\"{username}\\", \\"title\\": \\"Your Task Title\\", \\"description\\": \\"Description\\"}}"')
        print("\n   After assigning, login/logout again to see tasks")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
