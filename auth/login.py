# agent/auth/login.py

import logging
from werkzeug.security import check_password_hash
from auth.session import start_session, end_session, normalize_domain
from storage.db import get_connection

logger = logging.getLogger("LOGIN")


def login_user(email, password):

    conn = None

    try:
        # 🔹 Strip whitespace from both inputs
        email = email.strip()
        password = password.strip()

        print("====================================")
        print("LOGIN PROCESS STARTED")
        print(f"Username/Email entered: '{email}'")
        print(f"Password entered: '{password}'")
        print("====================================")

        # -------------------------------
        # CONNECT DATABASE
        # -------------------------------
        conn = get_connection()

        if not conn:
            print("❌ Database connection FAILED")
            return False

        print("✅ MySQL Database connection SUCCESS")
        cur = conn.cursor()

        print("📦 Fetching data from TABLE: users")

        # -------------------------------
        # FIND USER BY USERNAME OR EMAIL
        # -------------------------------
        cur.execute(
            """
            SELECT id, username, password, role, email, domain, designation
            FROM users
            WHERE LOWER(username) = LOWER(%s) OR LOWER(email) = LOWER(%s)
            """,
            (email, email),
        )

        user_record = cur.fetchone()

        print("🔎 Query executed")

        if not user_record:
            print(f"❌ No user found with this username or email: '{email}'")
            return False

        print("✅ User record fetched:")

        user_id, db_username, db_password, role, db_email, domain, designation = user_record

        # For debugging purposes. IMPORTANT: Remove in a production environment.
        print(f"   - DB Username: '{db_username}'")
        print(f"   - DB Password: '{db_password}'")

        # -------------------------------
        # PASSWORD CHECK
        # -------------------------------
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
            print(f"   - Entered: '{password}'")
            print(f"   - Expected: '{db_password}'")
            return False

    except Exception as e:
        print(f"🔥 LOGIN ERROR: {e}")
        logger.exception("An unexpected error occurred in the login function")
        return False

    finally:
        if conn:
            conn.close()
            print("📦 Database connection closed.")


def logout_user():
    end_session()
