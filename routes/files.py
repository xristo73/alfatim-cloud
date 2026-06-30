from flask import Blueprint, session, request, redirect, url_for, jsonify
from utils.decorators import login_required
from utils.paths import get_user_base_folder

import os
import shutil

files_bp = Blueprint("files", __name__)

# =====================================================
# ZMIANA NAZWY
# =====================================================

@files_bp.route("/rename", methods=["POST"])
def rename():

    if "username" not in session:
        return redirect(url_for("home"))

    current_path = request.form.get("current_path", "")
    old_name = request.form.get("old_name")
    new_name = request.form.get("new_name")
    print("OLD:", repr(old_name))
    print("NEW:", repr(new_name))
    print("PATH:", repr(current_path))

    if not old_name or not new_name:
        return redirect(url_for("dashboard", path=current_path))

    user_root = get_user_base_folder(session["username"])

    old_path = os.path.join(user_root, current_path, old_name)
    new_path = os.path.join(user_root, current_path, new_name)

    print("OLD PATH:", old_path)
    print("NEW PATH:", new_path)
    print("EXISTS:", os.path.exists(old_path))

    if os.path.exists(old_path):
        os.rename(old_path, new_path)

    return redirect(url_for("dashboard", path=current_path))

# =====================================================
# Kopiowanie plików i folderów
# =====================================================

@files_bp.route("/copy", methods=["POST"])
def copy():

    if "username" not in session:
        return redirect(url_for("home"))

    current_path = request.form.get("current_path", "")
    item_name = request.form.get("item_name")
    target_folder = request.form.get("target_folder", "").strip()

    if not item_name or not target_folder:
        return redirect(url_for("dashboard", path=current_path))

    user_root = get_user_base_folder(session["username"])

    source = os.path.join(user_root, current_path, item_name)
    destination_dir = os.path.join(user_root, target_folder)

    if os.path.exists(source) and os.path.isdir(destination_dir):

        destination = os.path.join(destination_dir, item_name)

        if os.path.isfile(source):
            shutil.copy2(source, destination)

        elif os.path.isdir(source):
            shutil.copytree(
                source,
                destination,
                dirs_exist_ok=True
            )

    return redirect(url_for("dashboard", path=current_path))

# =====================================================
# Przenoszenie poniedzy folderami
# ====================================================

@files_bp.route("/move", methods=["POST"])
def move():

    if "username" not in session:
        return redirect(url_for("home"))

    current_path = request.form.get("current_path", "")
    item_name = request.form.get("item_name")
    target_folder = request.form.get("target_folder", "").strip()

    if not item_name or not target_folder:
        return redirect(url_for("dashboard", path=current_path))

    user_root = get_user_base_folder(session["username"])

    source = os.path.join(user_root, current_path, item_name)
    destination_dir = os.path.join(user_root, target_folder)

    if os.path.exists(source) and os.path.isdir(destination_dir):
        shutil.move(
            source,
            os.path.join(destination_dir, item_name)
        )

    return redirect(url_for("dashboard", path=current_path))

@files_bp.route("/folders")
def folders():

    if "username" not in session:
        return jsonify([])

    user_root = get_user_base_folder(session["username"])

    result = []

    for root, dirs, files in os.walk(user_root):

        rel = os.path.relpath(root, user_root)

        if rel == ".":
            rel = ""

        result.append(rel)

    return jsonify(sorted(result))
