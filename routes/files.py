import os
import shutil
from werkzeug.utils import secure_filename
from flask import Blueprint, session, request, redirect, url_for, jsonify, flash, render_template, send_from_directory
from utils.decorators import login_required
from utils.paths import get_user_base_folder

files_bp = Blueprint("files", __name__)

# =====================================================
# ZMIANA NAZWY
# =====================================================

@files_bp.route("/rename", methods=["POST"])
def rename():

    if "username" not in session:
        return redirect(url_for("auth.home"))

    current_path = request.form.get("current_path", "")
    old_name = request.form.get("old_name")
    new_name = request.form.get("new_name")
    print("OLD:", repr(old_name))
    print("NEW:", repr(new_name))
    print("PATH:", repr(current_path))

    if not old_name or not new_name:
        return redirect(url_for("dashboard.dashboard", path=current_path))

    user_root = get_user_base_folder(session["username"])

    old_path = os.path.join(user_root, current_path, old_name)
    new_path = os.path.join(user_root, current_path, new_name)

    print("OLD PATH:", old_path)
    print("NEW PATH:", new_path)
    print("EXISTS:", os.path.exists(old_path))

    if os.path.exists(old_path):
        os.rename(old_path, new_path)

    return redirect(url_for("dashboard.dashboard", path=current_path))

# =====================================================
# Kopiowanie plików i folderów
# =====================================================

@files_bp.route("/copy", methods=["POST"])
def copy():

    if "username" not in session:
        return redirect(url_for("auth.home"))

    current_path = request.form.get("current_path", "")
    item_name = request.form.get("item_name")
    target_folder = request.form.get("target_folder", "").strip()

    if not item_name or not target_folder:
        return redirect(url_for("dashboard.dashboard", path=current_path))

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

    return redirect(url_for("dashboard.dashboard", path=current_path))

# =====================================================
# Przenoszenie poniedzy folderami
# ====================================================

@files_bp.route("/move", methods=["POST"])
def move():

    if "username" not in session:
        return redirect(url_for("auth.home"))

    current_path = request.form.get("current_path", "")
    item_name = request.form.get("item_name")
    target_folder = request.form.get("target_folder", "").strip()

    if not item_name or not target_folder:
        return redirect(url_for("dashboard.dashboard", path=current_path))

    user_root = get_user_base_folder(session["username"])

    source = os.path.join(user_root, current_path, item_name)
    destination_dir = os.path.join(user_root, target_folder)

    if os.path.exists(source) and os.path.isdir(destination_dir):
        shutil.move(
            source,
            os.path.join(destination_dir, item_name)
        )

    return redirect(url_for("dashboard.dashboard", path=current_path))

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

@files_bp.route("/create_folder", methods=["POST"])
@login_required
def create_folder():

    current_path = request.form.get("current_path", "")
    folder_name = secure_filename(request.form.get("folder_name", ""))

    # Nie pozwalaj tworzyć folderów w koszu
    if current_path == ".trash":
        return redirect(url_for("dashboard.dashboard", path=".trash"))

    # Pusta nazwa
    if not folder_name:
        return redirect(url_for("dashboard.dashboard", path=current_path))

    user_root = get_user_base_folder(session["username"])
    new_folder = os.path.join(user_root, current_path, folder_name)

    os.makedirs(new_folder, exist_ok=True)

    return redirect(url_for("dashboard.dashboard", path=current_path))


@files_bp.route("/delete")
@login_required
def delete():

    current_path = request.args.get("path", "")
    item_name = request.args.get("name")

    user_root = get_user_base_folder(session["username"])
    target = os.path.join(user_root, current_path, item_name)

    trash_dir = os.path.join(user_root, ".trash")
    os.makedirs(trash_dir, exist_ok=True)

    destination = os.path.join(trash_dir, item_name)

    counter = 1
    while os.path.exists(destination):
        destination = os.path.join(
            trash_dir,
            f"{counter}_{item_name}"
        )

    shutil.move(target, destination)

    return redirect(url_for("dashboard.dashboard", path=current_path))


@files_bp.route("/view")
@login_required
def view_file():

    current_path = request.args.get("path", "")
    filename = request.args.get("name")

    user_root = get_user_base_folder(session["username"])
    folder = os.path.join(user_root, current_path)

    # Pełna ścieżka do pliku dla szablonu
    filepath = os.path.join(current_path, filename) if current_path else filename

    # Pobieramy WSZYSTKIE pliki z folderu (tak jak w dashboardzie, ale bez folderów)
    files = []
    if os.path.exists(folder):
        items = os.listdir(folder)
        # Filtrujemy tylko pliki (pomijamy foldery)
        files = sorted([
            f for f in items 
            if os.path.isfile(os.path.join(folder, f))
        ])

        file_content = None

        if filename:
            full_file = os.path.join(folder, filename)

            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

            if ext in ["txt", "py", "html", "css", "js", "json", "log", "md", "xml", "yaml", "yml"]:
                try:
                    with open(full_file, "r", encoding="utf-8", errors="ignore") as f:
                        file_content = f.read()
                except:
                    file_content = "Nie można odczytać pliku."

    return render_template(
        "preview.html",
        filepath=filepath,      # Ścieżka dla img src / iframe
        filename=filename,      # Sama nazwa do znalezienia w liście JS
        current_path=current_path,
        files=files,             # Lista nazw wszystkich plików w folderze
        file_content=file_content
    )


@files_bp.route("/file/<path:filepath>")
@login_required
def serve_file(filepath):

    user_root = get_user_base_folder(session["username"])


    folder = os.path.dirname(filepath)
    filename = os.path.basename(filepath)

    return send_from_directory(
        os.path.join(user_root, folder),
        filename
    )

@files_bp.route("/download/<path:filepath>")
@login_required
def download(filepath):

    user_root = get_user_base_folder(session["username"])

    folder = os.path.dirname(filepath)
    filename = os.path.basename(filepath)

    return send_from_directory(
        os.path.join(user_root, folder),
        filename,
        as_attachment=True
    )
