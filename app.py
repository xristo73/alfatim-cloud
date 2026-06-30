
from flask import Flask, render_template, request, redirect, url_for, session, abort, send_from_directory, send_file, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
from database import init_db, get_db, close_db
from utils.validators import allowed_file
from utils.paths import get_user_base_folder, secure_user_path
from utils.security import is_logged_in, is_admin
from utils.helpers import get_folder_size, generate_thumb
from routes.auth import auth_bp
from routes.sharing import sharing_bp
from routes.clipboard import clipboard_bp
from services.user_service import get_user, get_user_limit
from utils.decorators import login_required, admin_required
from routes.trash import trash_bp
from routes.upload import upload_bp
from routes.download import download_bp
from routes.files import files_bp
from routes.bulk import bulk_bp
from routes.admin import admin_bp
import os
import sqlite3
import shutil
import time 
import secrets
import config
app = Flask(__name__)
app.register_blueprint(auth_bp)
app.register_blueprint(sharing_bp)
app.register_blueprint(clipboard_bp)
app.register_blueprint(trash_bp)
app.secret_key = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
app.teardown_appcontext(close_db)
app.register_blueprint(upload_bp)
app.register_blueprint(download_bp)
app.register_blueprint(files_bp)
app.register_blueprint(bulk_bp)
app.register_blueprint(admin_bp)
UPLOAD_FOLDER = config.UPLOAD_FOLDER
DATABASE = config.DATABASE
ALLOWED_EXTENSIONS = config.ALLOWED_EXTENSIONS

init_db()


# =====================================================
# POMOCNICZE
# =====================================================


# =====================================================
# AUTH
# =====================================================

@app.route("/")
def home():
    if is_logged_in():
        return redirect(url_for("dashboard"))
    return render_template("auth.html")


@app.route("/login", methods=["POST"])
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

            return redirect(url_for("dashboard"))

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


@app.route("/register", methods=["POST"])
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


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# =====================================================
# zobacz plik
# =====================================================

@app.route("/view")
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


@app.route("/file/<path:filepath>")
@login_required
def serve_file(filepath):

    user_root = get_user_base_folder(session["username"])


    folder = os.path.dirname(filepath)
    filename = os.path.basename(filepath)

    return send_from_directory(
        os.path.join(user_root, folder),
        filename
    )

@app.route("/download/<path:filepath>")
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

# =====================================================
# Tworzenie folderu
# =====================================================

@app.route("/create_folder", methods=["POST"])
def create_folder():
    if "username" not in session:
        return redirect(url_for("home"))

    folder_name = secure_filename(request.form.get("folder_name"))
    current_path = request.form.get("current_path", "")

    user_root = get_user_base_folder(session["username"])
    new_folder = os.path.join(user_root, current_path, folder_name)

    os.makedirs(new_folder, exist_ok=True)

    return redirect(url_for("dashboard", path=current_path))

# =====================================================
# Usuwanie Folderu
# =====================================================

@app.route("/delete")
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
        counter += 1

    shutil.move(target, destination)

    return redirect(url_for("dashboard", path=current_path))

# =====================================================
# Przywracanie z kosza
# =====================================================


# =====================================================
# Opróżnij kosz
# =====================================================

@app.route("/empty_trash", methods=["POST"])
@login_required
def empty_trash():

    user_root = get_user_base_folder(session["username"])
    trash_dir = os.path.join(user_root, ".trash")

    if os.path.isdir(trash_dir):

        for item in os.listdir(trash_dir):

            path = os.path.join(trash_dir, item)

            if os.path.isdir(path):
                shutil.rmtree(path)

            else:
                os.remove(path)

    return redirect(url_for("dashboard", path=".trash"))

# =====================================================
# Przywracanie wersji pliku
# =====================================================

@app.route("/restore_version")
@login_required
def restore_version():

    filename = request.args.get("name")
    version = request.args.get("version")

    user_root = get_user_base_folder(session["username"])

    current_file = os.path.join(user_root, filename)
    version_file = os.path.join(
        user_root,
        ".versions",
        version
    )

    if os.path.exists(version_file):

        if os.path.exists(current_file):

            from datetime import datetime

            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )

            backup = os.path.join(
                user_root,
                ".versions",
                f"{os.path.basename(filename)}_{timestamp}"
            )

            shutil.copy2(current_file, backup)

        shutil.copy2(version_file, current_file)

    return redirect(url_for("dashboard"))

# =====================================================
# WYSZUKIWARKA
# =====================================================

@app.route("/search")
@login_required
def search():

    query = request.args.get("q", "").lower()

    user_root = get_user_base_folder(session["username"])

    results = []

    for root, dirs, files in os.walk(user_root):

        for folder in dirs:
            if query in folder.lower():
                rel_path = os.path.relpath(
                    os.path.join(root, folder),
                    user_root
                )

                results.append({
                    "name": folder,
                    "path": rel_path,
                    "is_folder": True
                })

        for file in files:
            if query in file.lower():

                rel_path = os.path.relpath(
                    os.path.join(root, file),
                    user_root
                )

                results.append({
                    "name": file,
                    "path": rel_path,
                    "is_folder": False
                })

    return render_template(
        "search.html",
        results=results,
        query=query
    )
 
# =====================================================
# DASHBOARD
# =====================================================

@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect(url_for("home"))

    current_path = request.args.get("path", "")
    user_root = get_user_base_folder(session["username"])
    full_path = os.path.join(user_root, current_path)

    if not os.path.exists(full_path):
        return redirect(url_for("dashboard"))

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

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)


# =====================================================
# Lista wersji pliku
# =====================================================

@app.route("/versions")
def show_versions():

    if "username" not in session:
        return redirect(url_for("home"))

    filename = request.args.get("name")

    user_root = get_user_base_folder(session["username"])
    versions_dir = os.path.join(user_root, ".versions")

    versions = []

    if os.path.exists(versions_dir):

        for f in sorted(os.listdir(versions_dir), reverse=True):

            if f.startswith(filename + "_"):

                versions.append(f)

    html = f"<h2>Wersje pliku: {filename}</h2><hr>"

    if not versions:
        html += "<p>Brak zapisanych wersji.</p>"

    for v in versions:

        html += f"""
        <p>
            {v}
            <a href="/restore_version?name={filename}&version={v}">
                [Przywróć]
            </a>
        </p>
        """

    html += '<br><a href="/dashboard">Powrót</a>'

    return html

# =====================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
