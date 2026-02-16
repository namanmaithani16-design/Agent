# agent/auth/login.py

from auth.session import start_session, end_session

# Dummy user authentication (no DB)
USERS = {
    "admin": {"password": "123", "role": "admin"},
    "employee": {"password": "123", "role": "employee"},
}


def login_user(username, password):
    user = USERS.get(username)

    if user and user["password"] == password:
        start_session(
            user_id=1,
            username=username,
            role=user["role"]
        )
        return True

    return False


def logout_user():
    end_session()
