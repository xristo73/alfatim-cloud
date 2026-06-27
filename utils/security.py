from flask import session


def is_logged_in():
    return "user_id" in session


def is_admin():
    return session.get("role") == "admin"
