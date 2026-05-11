#!/usr/bin/env python3
"""
Test script to check user status via the new API endpoints.

Usage:
    python test_user_status.py --username <username>
    python test_user_status.py --all                    # Get all active users
    python test_user_status.py --role USER             # Get users by role
"""

import requests
import json
import argparse
import sys
from datetime import datetime

API_BASE_URL = "http://localhost:5000"

def get_user_status(username):
    """Get the online/offline status of a specific user."""
    endpoint = f"{API_BASE_URL}/api/user-status?username={username}"
    
    print(f"📊 Getting status for: {username}")
    print(f"   Endpoint: {endpoint}")
    print()
    
    try:
        response = requests.get(endpoint, timeout=10)
        response_data = response.json()
        
        if response.status_code == 200:
            data = response_data
            status = data.get("status")
            status_emoji = "🟢" if status == "online" else "🔴"
            
            print(f"{status_emoji} Status: {status.upper()}")
            print(f"   Action: {data.get('action')}")
            print(f"   Login Time: {data.get('login_time') or 'N/A'}")
            print(f"   Last Activity: {data.get('last_activity') or 'N/A'}")
            print(f"   Email: {data.get('email') or 'N/A'}")
            print(f"   Domain: {data.get('domain') or 'N/A'}")
            print(f"   Designation: {data.get('designation') or 'N/A'}")
            return True
        else:
            print(f"❌ Failed to get status")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {json.dumps(response_data, indent=2)}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Cannot reach {API_BASE_URL}")
        print("   Make sure your Flask server is running")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def get_all_active_users(role_filter=None):
    """Get all active users, optionally filtered by role."""
    endpoint = f"{API_BASE_URL}/api/active-users"
    if role_filter:
        endpoint += f"?role={role_filter}"
    
    role_text = f" (Role: {role_filter})" if role_filter else ""
    print(f"👥 Getting all active users{role_text}")
    print(f"   Endpoint: {endpoint}")
    print()
    
    try:
        response = requests.get(endpoint, timeout=10)
        response_data = response.json()
        
        if response.status_code == 200:
            users = response_data.get("users", [])
            total = response_data.get("total", 0)
            
            print(f"✅ Found {total} user(s)")
            print()
            
            if not users:
                print("   No users found")
                return True
            
            # Create formatted table
            print(f"{'Username':<20} {'Status':<10} {'Action':<10} {'Role':<15} {'Last Activity':<20}")
            print("-" * 75)
            
            for user in users:
                username = user.get("username", "N/A")
                status = user.get("status", "unknown")
                action = user.get("action", "N/A")
                role = user.get("role", "N/A")
                last_activity = user.get("last_activity", "N/A")
                
                status_emoji = "🟢" if status == "online" else "🔴"
                
                print(f"{username:<20} {status_emoji} {status:<8} {action:<10} {role:<15} {last_activity:<20}")
            
            return True
        else:
            print(f"❌ Failed to fetch users")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {json.dumps(response_data, indent=2)}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Cannot reach {API_BASE_URL}")
        print("   Make sure your Flask server is running")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Check user online/offline status",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check status of a specific user
  python test_user_status.py --username john_intern
  
  # Get all active users
  python test_user_status.py --all
  
  # Get all active users with role=USER
  python test_user_status.py --all --role USER
  
  # Interactive mode
  python test_user_status.py --interactive
        """
    )
    
    parser.add_argument("--username", help="Check status of a specific user")
    parser.add_argument("--all", action="store_true", help="Get all active users")
    parser.add_argument("--role", help="Filter by role (used with --all)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    if args.interactive:
        # Interactive mode
        print("\n🔍 User Status Checker - Interactive Mode")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("  1. Check specific user status")
            print("  2. Get all active users")
            print("  3. Get active users by role")
            print("  4. Exit")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                username = input("Enter username: ").strip()
                if username:
                    get_user_status(username)
                else:
                    print("❌ Username is required")
                    
            elif choice == "2":
                print()
                get_all_active_users()
                
            elif choice == "3":
                role = input("Enter role (e.g., USER, ADMIN): ").strip()
                if role:
                    print()
                    get_all_active_users(role)
                else:
                    print("❌ Role is required")
                    
            elif choice == "4":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option")
                
    elif args.username:
        get_user_status(args.username)
    elif args.all:
        get_all_active_users(args.role)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
