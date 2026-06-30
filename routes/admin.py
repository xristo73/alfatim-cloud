import os
import sqlite3
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    abort,
    flash
)

from database import get_db
from utils.security import is_logged_in, is_admin
from werkzeug.security import generate_password_hash
from config import UPLOAD_FOLDER

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin")
def admin_panel():
    if not is_logged_in() or not is_admin():
        abort(403)

    db = get_db()
    c = db.cursor()
    c.execute("SELECT id, username, role, storage_limit FROM users")
    users = c.fetchall()

    return render_template(
        "admin.html",
        users=users,
        total_users=len(users)
    )

@admin_bp.route("/admin/add_user", methods=["POST"])
def add_user():
    if not is_logged_in() or not is_admin():
        abort(403)

    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role", "user")

    if not username or not password:
        flash("Brak danych do utworzenia użytkownika", "error")
        return redirect(url_for("admin.admin_panel"))

    hashed_password = generate_password_hash(password)

    try:
        storage_limit = float(request.form.get("storage_limit", 100))
        if storage_limit <= 0:
            storage_limit = 100
    except:
        storage_limit = 100

    db = get_db()
    c = db.cursor()

    try:
        c.execute("""
            INSERT INTO users (username, password, role, storage_limit)
            VALUES (?, ?, ?, ?)
        """, (username, hashed_password, role, storage_limit))

        db.commit()

        os.makedirs(os.path.join(UPLOAD_FOLDER, username), exist_ok=True)

        flash(f"Użytkownik {username} został utworzony", "success")

    except sqlite3.IntegrityError:
        flash("Użytkownik już istnieje", "error")

    return redirect(url_for("admin.admin_panel"))


@admin_bp.route("/admin/delete_user", methods=["POST"])
def delete_user():
    if not is_logged_in() or not is_admin():
        abort(403)

    username = request.form.get("username")

    if not username:
        return "Brak użytkownika", 400

    if username == session.get("username"):
        return "Nie możesz usunąć samego siebie", 400

    db = get_db()
    c = db.cursor()

    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = c.fetchone()

    if not user:
        return "Użytkownik nie istnieje", 404

    c.execute("DELETE FROM users WHERE username = ?", (username,))
    db.commit()

    user_folder = os.path.join(UPLOAD_FOLDER, username)
    if os.path.exists(user_folder):
        shutil.rmtree(user_folder)

    return redirect(url_for("admin.admin_panel"))

@admin_bp.route("/admin/update_limit/<int:user_id>", methods=["POST"])
def update_limit(user_id):
    if not is_logged_in() or not is_admin():
        abort(403)

    try:
        new_limit = float(request.form.get("storage_limit"))
        if new_limit <= 0:
            new_limit = 100
    except:
        new_limit = 100

    db = get_db()
    c = db.cursor()
    c.execute(
        "UPDATE users SET storage_limit = ? WHERE id = ?",
        (new_limit, user_id)
    )
    db.commit()

    return redirect(url_for("admin.admin_panel"))
