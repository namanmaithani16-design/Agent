"""
Quick Testing Script for Task Management System

This script helps you test the task assignment and display functionality.
Run this to assign demo tasks to your account.
"""

import sys
sys.path.insert(0, r'c:\Users\naman\OneDrive\Desktop\agent')

from storage.db import assign_demo_tasks, debug_all_tasks, debug_current_user
from auth.session import get_current_user

def main():
    print("\n" + "="*60)
    print("  TASK MANAGEMENT SYSTEM - TEST UTILITY")
    print("="*60 + "\n")
    
    # Check current user
    print("🔍 Checking current user...")
    debug_current_user()
    
    current_user = get_current_user()
    if not current_user:
        print("\n⚠️  No user logged in!")
        print("❌ Please login first before assigning tasks.\n")
        return
    
    username = current_user.get("username")
    
    # Show all tasks
    print("\n" + "-"*60)
    print("📊 Current tasks in database:")
    print("-"*60)
    debug_all_tasks()
    
    # Prompt to assign demo tasks
    print("\n" + "-"*60)
    response = input(f"❓ Assign 5 demo tasks to '{username}'? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print("\n📝 Assigning demo tasks...")
        if assign_demo_tasks(username):
            print("✅ Demo tasks assigned successfully!")
            
            # Show updated tasks
            print("\n" + "-"*60)
            print("📊 Tasks after assignment:")
            print("-"*60)
            debug_all_tasks()
            
            print("\n✨ Now login again and check the logout window to see your tasks!")
        else:
            print("❌ Failed to assign demo tasks")
    else:
        print("\n⏭️  Skipped task assignment.\n")

if __name__ == "__main__":
    main()
