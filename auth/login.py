# agent/auth/login.py

import logging

from werkzeug.security import check_password_hash

from auth.session import end_session, normalize_domain, start_session
from storage.db import get_mysql_connection

logger = logging.getLogger("LOGIN")


def _find_account(cursor, login_value):
    for table_name in ("users", "admins"):
        cursor.execute(
            f"""
            SELECT id, username, password, role, email, domain, designation,
                   %s AS account_type
            FROM {table_name}
            WHERE LOWER(username) = LOWER(%s) OR LOWER(email) = LOWER(%s)
            LIMIT 1
            """,
            (table_name, login_value, login_value),
        )
        account = cursor.fetchone()
        if account:
            return account

    return None


def login_user(email, password):
    conn = None
    cur = None

    try:
        login_value = email.strip()
        password = password.strip()

        print("====================================")
        print("LOGIN PROCESS STARTED")
        print(f"Username/Email entered: '{login_value}'")
        print("====================================")

        conn = get_mysql_connection()
        cur = conn.cursor(dictionary=True)

        account = _find_account(cur, login_value)
        if not account:
            print(f"No account found: '{login_value}'")
            return False

        print(
            f"Account found in {account.get('account_type')}: "
            f"'{account.get('username')}' | Role: '{account.get('role')}'"
        )

        if not check_password_hash(account.get("password") or "", password):
            print("Incorrect password.")
            return False

        print("Password matches. Login successful.")

        start_session(
            user_id=account.get("id"),
            username=account.get("username"),
            role=account.get("role"),
            email=account.get("email"),
            domain=normalize_domain(account.get("domain")),
            designation=account.get("designation"),
        )
        return True

    except Exception as e:
        print(f"LOGIN ERROR: {e}")
        logger.exception("Login error")
        return False

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("Database connection closed.")


def logout_user():
    end_session()
