from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from utils.security import is_logged_in
from services.user_service import get_user
import time
from database import get_db
from config import UPLOAD_FOLDER

import os

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def home():
    if is_logged_in():
        return redirect(url_for("dashboard.dashboard"))
    return render_template("auth.html")


@auth_bp.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    user = get_user(username)
    current_time = int(time.time())

    if user:
        # blokada
        if user[6] and user[6] > current_time:
            return render_template("auth.html", error="Konto zablokowane na 5 minut.")

        if check_password_hash(user[2], password):

            db = get_db()
            c = db.cursor()
            c.execute("UPDATE users SET failed_attempts=0 WHERE id=?", (user[0],))
            db.commit()
            session["user_id"] = user[0]
            session["username"] = user[1]
            session["role"] = user[3]

            return redirect(url_for("dashboard.dashboard"))

        else:
            
            db = get_db()
            c = db.cursor()

            new_attempts = user[5] + 1
            block_time = 0

            if new_attempts >= 5:
                block_time = current_time + 300
                new_attempts = 0

            c.execute("""
                UPDATE users
                SET failed_attempts=?, blocked_until=?
                WHERE id=?
            """, (new_attempts, block_time, user[0]))

            db.commit()

            return render_template("auth.html", error="Nieprawidłowy login lub hasło.")

    return render_template("auth.html", error="Nieprawidłowy login lub hasło.")


@auth_bp.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        return render_template("auth.html", error="Wypełnij wszystkie pola.")

    hashed = generate_password_hash(password)

    try:
        db = get_db()
        c = db.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        db.commit()

        get_user_base_folder(username)

        return render_template("auth.html", success="Konto utworzone. Możesz się zalogować.")

    except sqlite3.IntegrityError:
        return render_template("auth.html", error="Użytkownik już istnieje.")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.home"))
