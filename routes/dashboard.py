from flask import Blueprint, render_template, request, redirect, url_for, session, send_from_directory
from utils.decorators import login_required
from utils.paths import get_user_base_folder
from database import get_db

import os

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():

    if "username" not in session:
        return redirect(url_for("auth.home"))

    current_path = request.args.get("path", "")
    user_root = get_user_base_folder(session["username"])
    full_path = os.path.join(user_root, current_path)

    if not os.path.exists(full_path):
        return redirect(url_for("dashboard.dashboard"))

    items = []

    if current_path == "":
        items.append({
            "name": "🗑 Kosz",
            "is_folder": True
        })

    for item in os.listdir(full_path):
        item_path = os.path.join(full_path, item)
        items.append({
            "name": item,
            "is_folder": os.path.isdir(item_path)
        })    

    # 🔥 liczenie zajętego miejsca (w MB)
    total_size = 0
    for root, dirs, files in os.walk(user_root):
        for f in files:
            try:
                total_size += os.path.getsize(os.path.join(root, f))
            except:
                pass

    storage_used = round(total_size / (1024 * 1024), 2)

    # 🔥 pobranie limitu z bazy (w MB)
    db = get_db()
    c = db.cursor()
    c.execute(
        "SELECT storage_limit FROM users WHERE username = ?",
        (session["username"],)
    )
    result = c.fetchone()

    storage_limit = round(result[0], 2) if result else 100

    # 🔥 procent wykorzystania
    if storage_limit > 0:
        usage_percent = round((storage_used / storage_limit) * 100, 1)
    else:
        usage_percent = 0

    return render_template(
        "index.html",
        items=items,
        current_path=current_path,
        storage_used=storage_used,
        storage_limit=storage_limit,
        usage_percent=usage_percent,
        in_trash=(current_path == ".trash")
    )
