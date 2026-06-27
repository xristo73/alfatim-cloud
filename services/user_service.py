from database import get_db


def get_user(username):
    db = get_db()
    c = db.cursor()

    c.execute("""
        SELECT id, username, password, role, storage_limit,
               failed_attempts, blocked_until
        FROM users
        WHERE username = ?
    """, (username,))

    return c.fetchone()


def get_user_limit(user_id):
    db = get_db()
    c = db.cursor()

    c.execute(
        "SELECT storage_limit FROM users WHERE id = ?",
        (user_id,)
    )

    result = c.fetchone()

    return result[0] if result else 0
