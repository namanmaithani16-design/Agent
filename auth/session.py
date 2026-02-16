# agent/auth/session.py

import logging

logger = logging.getLogger("SESSION")

_session_active = False
_current_user = None


# =============================
# SESSION CONTROL
# =============================

def start_session(user_id, username, role):
    """
    Start user session
    """
    global _session_active, _current_user

    _session_active = True
    _current_user = {
        "user_id": user_id,
        "username": username,
        "role": role
    }

    logger.info(f"Session started for {username}")


def end_session():
    """
    End current session
    """
    global _session_active, _current_user

    if _current_user:
        logger.info(f"Session ended for {_current_user.get('username')}")

    _session_active = False
    _current_user = None


# =============================
# SESSION STATUS
# =============================

def is_active():
    """
    Check if session is active
    """
    return _session_active


# =============================
# USER ACCESSORS
# =============================

def get_current_user():
    """
    Preferred function to get logged-in user
    """
    return _current_user


# 🔥 IMPORTANT: Backward compatibility
# Some files are importing get_user()
# So we expose alias to avoid ImportError

def get_user():
    """
    Alias for compatibility with old imports
    """
    return _current_user
