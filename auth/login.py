# agent/auth/login.py

import logging
from werkzeug.security import check_password_hash
from auth.session import start_session, end_session, normalize_domain
from storage.db import get_mysql_connection

logger = logging.getLogger("LOGIN")


def login_user(email, password):
    conn = None
    try:
        email = email.strip()
        password = password.strip()

        print("====================================")
        print("LOGIN PROCESS STARTED")
        print(f"Username/Email entered: '{email}'")
        print("====================================")

        # ✅ FIXED: Use MySQL connection instead of SQLite
        conn = get_mysql_connection()

        if not conn:
            print("❌ Database connection FAILED")
            return False

        print("✅ MySQL Database connection SUCCESS")
        cur = conn.cursor()

        print("📦 Fetching data from TABLE: users")

        cur.execute(
            """
            SELECT id, username, password, role, email, domain, designation
            FROM users
            WHERE LOWER(username) = LOWER(%s) OR LOWER(email) = LOWER(%s)
            """,
            (email, email),
        )

        user_record = cur.fetchone()

        if not user_record:
            print(f"❌ No user found: '{email}'")
            return False

        user_id, db_username, db_password, role, db_email, domain, designation = user_record

        print(f"✅ User found: '{db_username}' | Role: '{role}'")

        if check_password_hash(db_password, password):
            print("✅ Password matches. Login successful.")

            domain = normalize_domain(domain)
            start_session(
                user_id=user_id,
                username=db_username,
                role=role,
                email=db_email,
                domain=domain,
                designation=designation,
            )
            return True
        else:
            print("❌ Incorrect password.")
            return False

    except Exception as e:
        print(f"🔥 LOGIN ERROR: {e}")
        logger.exception("Login error")
        return False

    finally:
        if conn:
            conn.close()
            print("📦 Database connection closed.")


def logout_user():
    end_session()