from flask import Flask, render_template, request, redirect, url_for, session, abort, send_from_directory, send_file, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
from database import init_db, get_db, close_db
from utils.validators import allowed_file
from utils.paths import get_user_base_folder, secure_user_path
from utils.security import is_logged_in, is_admin
from utils.helpers import get_folder_size, generate_thumb
from routes.auth import auth_bp
from services.user_service import get_user, get_user_limit
import os
import sqlite3
import shutil
import time 
import secrets
import config
app = Flask(__name__)
app.register_blueprint(auth_bp)
app.secret_key = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
app.teardown_appcontext(close_db)
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
def view_file():
    if "username" not in session:
        return redirect(url_for("home"))

    current_path = request.args.get("path", "")
    filename = request.args.get("name")

    user_root = os.path.join("uploads", session["username"])
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
def serve_file(filepath):

    if "username" not in session:
        return redirect(url_for("home"))

    user_root = os.path.join("uploads", session["username"])

    folder = os.path.dirname(filepath)
    filename = os.path.basename(filepath)

    return send_from_directory(
        os.path.join(user_root, folder),
        filename
    )

@app.route("/download/<path:filepath>")
def download(filepath):

    if "username" not in session:
        return redirect(url_for("home"))

    user_root = os.path.join("uploads", session["username"])

    folder = os.path.dirname(filepath)
    filename = os.path.basename(filepath)

    return send_from_directory(
        os.path.join(user_root, folder),
        filename,
        as_attachment=True
    )

# ====================================================
# Pobieranie
# ====================================================

@app.route("/download")
def download_file():

    print("DOWNLOAD_FILE")

    if "username" not in session:
        return redirect(url_for("home"))

    current_path = request.args.get("path", "")
    filename = request.args.get("name")

    user_root = os.path.join("uploads", session["username"])
    folder = os.path.join(user_root, current_path)

    return send_from_directory(
        folder,
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

    user_root = os.path.join("uploads", session["username"])
    new_folder = os.path.join(user_root, current_path, folder_name)

    os.makedirs(new_folder, exist_ok=True)

    return redirect(url_for("dashboard", path=current_path))

# =====================================================
# Usuwanie Folderu
# =====================================================

@app.route("/delete")
def delete():
    if "username" not in session:
        return redirect(url_for("home"))

    current_path = request.args.get("path", "")
    item_name = request.args.get("name")

    user_root = os.path.join("uploads", session["username"])
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

@app.route("/restore")
def restore():

    if "username" not in session:
        return redirect(url_for("home"))

    item_name = request.args.get("name")

    user_root = os.path.join("uploads", session["username"])

    source = os.path.join(user_root, ".trash", item_name)
    destination = os.path.join(user_root, item_name)

    if os.path.exists(source):
        shutil.move(source, destination)

    return redirect(url_for("dashboard", path=".trash"))

# =====================================================
# Przywracanie wersji pliku
# =====================================================

@app.route("/restore_version")
def restore_version():

    if "username" not in session:
        return redirect(url_for("home"))

    filename = request.args.get("name")
    version = request.args.get("version")

    user_root = os.path.join("uploads", session["username"])

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
def search():

    if "username" not in session:
        return redirect(url_for("home"))

    query = request.args.get("q", "").lower()

    user_root = os.path.join("uploads", session["username"])

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
# Udostępnianie plików
# =====================================================

@app.route("/share_create")
def share_create():

    if "username" not in session:
        return redirect(url_for("home"))

    current_path = request.args.get("path", "")
    item_name = request.args.get("name")

    filepath = os.path.join(
        session["username"],
        current_path,
        item_name
    )

    token = secrets.token_hex(16)

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute(
        "INSERT INTO shared_links (token, filepath) VALUES (?, ?)",
        (token, filepath)
    )

    conn.commit()
    conn.close()

    flash(
        f"https://chmura.alfatim.pl/share/{token}",
        "success"
    )

    return redirect(url_for("dashboard", path=current_path))

@app.route("/share/<token>")
def share_file(token):

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute(
        "SELECT filepath FROM shared_links WHERE token=?",
        (token,)
    )

    result = c.fetchone()
    conn.close()

    if not result:
        abort(404)

    filepath = result[0]

    folder = os.path.dirname(filepath)
    filename = os.path.basename(filepath)

    return send_from_directory(
        os.path.join("uploads", folder),
        filename,
        as_attachment=True
    )

# =====================================================
# ZMIANA NAZWY
# =====================================================

@app.route("/rename", methods=["POST"])
def rename():

    if "username" not in session:
        return redirect(url_for("home"))

    current_path = request.form.get("current_path", "")
    old_name = request.form.get("old_name")
    new_name = request.form.get("new_name")

    if not old_name or not new_name:
        return redirect(url_for("dashboard", path=current_path))

    user_root = os.path.join("uploads", session["username"])

    old_path = os.path.join(user_root, current_path, old_name)
    new_path = os.path.join(user_root, current_path, new_name)

    if os.path.exists(old_path):
        os.rename(old_path, new_path)

    return redirect(url_for("dashboard", path=current_path))

# =====================================================
# Kopiowanie plików i folderów
# =====================================================

@app.route("/copy", methods=["POST"])
def copy():

    if "username" not in session:
        return redirect(url_for("home"))

    current_path = request.form.get("current_path", "")
    item_name = request.form.get("item_name")
    target_folder = request.form.get("target_folder", "").strip()

    if not item_name or not target_folder:
        return redirect(url_for("dashboard", path=current_path))

    user_root = os.path.join("uploads", session["username"])

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
# Schowek - kopiuj
# =====================================================

@app.route("/clipboard_copy", methods=["POST"])
def clipboard_copy():

    if "username" not in session:
        return redirect(url_for("home"))

    import json

    session["clipboard"] = {
        "action": "copy",
        "current_path": request.form.get("current_path", ""),
        "items": json.loads(
            request.form.get("items", "[]")
        )
    }

    return "OK"

# =====================================================
# Schowek - wklej
# =====================================================

@app.route("/clipboard_paste", methods=["POST"])
def clipboard_paste():

    if "username" not in session:
        return redirect(url_for("home"))

    clipboard = session.get("clipboard")

    if not clipboard:
        return redirect(url_for("dashboard"))

    user_root = os.path.join(
        "uploads",
        session["username"]
    )

    target_path = request.form.get(
        "current_path",
        ""
    )

    destination_dir = os.path.join(
        user_root,
        target_path
    )

    source_path = clipboard["current_path"]

    for item_name in clipboard["items"]:

        source = os.path.join(
            user_root,
            source_path,
            item_name
        )

        destination = os.path.join(
            destination_dir,
            item_name
        )

        if os.path.isfile(source):

            shutil.copy2(
                source,
                destination
            )

        elif os.path.isdir(source):

            shutil.copytree(
                source,
                destination,
                dirs_exist_ok=True
            )

    return redirect(
        url_for(
            "dashboard",
            path=target_path
        )
    )


# =====================================================
# Kopiowanie wielu elementów
# =====================================================

@app.route("/bulk_copy", methods=["POST"])
def bulk_copy():

    if "username" not in session:
        return redirect(url_for("home"))

    import json

    current_path = request.form.get("current_path", "")
    target_folder = request.form.get("target_folder", "")

    items = json.loads(
        request.form.get("items", "[]")
    )

    user_root = os.path.join(
        "uploads",
        session["username"]
    )

    destination_dir = os.path.join(
        user_root,
        target_folder
    )

    if not os.path.isdir(destination_dir):
        return redirect(
            url_for(
                "dashboard",
                path=current_path
            )
        )

    for item_name in items:

        source = os.path.join(
            user_root,
            current_path,
            item_name
        )

        destination = os.path.join(
            destination_dir,
            item_name
        )

        if os.path.isfile(source):

            shutil.copy2(
                source,
                destination
            )

        elif os.path.isdir(source):

            shutil.copytree(
                source,
                destination,
                dirs_exist_ok=True
            )

    return redirect(
        url_for(
            "dashboard",
            path=current_path
        )
    )

# =====================================================
# Pobieranie ZIP wielu plików
# =====================================================

@app.route("/bulk_zip", methods=["POST"])
def bulk_zip():

    app.logger.error("BULK ZIP CALLED")
    current_path = request.form.get("current_path", "")

    if "username" not in session:
        return redirect(url_for("home"))

    import json
    import tempfile
    import zipfile

    current_path = request.form.get("current_path", "")

    items = json.loads(
        request.form.get("items", "[]")
    )

    user_root = os.path.join(
        "uploads",
        session["username"]
    )

    temp_zip = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".zip"
    )

    with zipfile.ZipFile(
        temp_zip.name,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zipf:

        for item_name in items:

            item_path = os.path.join(
                user_root,
                current_path,
                item_name
            )

            if os.path.isfile(item_path):

                zipf.write(
                    item_path,
                    arcname=item_name
                )

            elif os.path.isdir(item_path):

                for root, dirs, files in os.walk(item_path):

                    for file in files:

                        full_path = os.path.join(
                            root,
                            file
                        )

                        arcname = os.path.relpath(
                            full_path,
                            os.path.join(
                                user_root,
                                current_path
                            )
                        )

                        zipf.write(
                            full_path,
                            arcname=arcname
                        )

    app.logger.error(f"ZIP FILE: {temp_zip.name}")
    app.logger.error(f"ZIP EXISTS: {os.path.exists(temp_zip.name)}")
    app.logger.error(f"ZIP SIZE: {os.path.getsize(temp_zip.name)}") 

    return send_file(
        temp_zip.name,
        mimetype="application/zip",
        as_attachment=True,
        download_name="pobrane.zip"
    )

# =====================================================
# Przenoszenie wielu elementów
# =====================================================

@app.route("/bulk_move", methods=["POST"])
def bulk_move():

    if "username" not in session:
        return redirect(url_for("home"))

    import json
    target_folder = request.form.get("target_folder", "")

    items = json.loads(
        request.form.get("items", "[]")
    )

    user_root = os.path.join(
        "uploads",
        session["username"]
    )

    destination_dir = os.path.join(
        user_root,
        target_folder
    )

    if not os.path.isdir(destination_dir):
        return redirect(
            url_for(
                "dashboard",
                path=current_path
            )
        )

    for item_name in items:

        source = os.path.join(
            user_root,
            current_path,
            item_name
        )

        destination = os.path.join(
            destination_dir,
            item_name
        )

        if os.path.exists(source):
            shutil.move(
                source,
                destination
            )

    return redirect(
        url_for(
            "dashboard",
            path=current_path
        )
    )

# =====================================================
# Usuwanie wielu elementów
# =====================================================

@app.route("/bulk_delete", methods=["POST"])
def bulk_delete():

    if "username" not in session:
        return redirect(url_for("home"))

    import json

    current_path = request.form.get(
        "current_path",
        ""
    )
    
    raw_items = request.form.get("items", "")

    print("ITEMS_RAW:", repr(raw_items))

    try:
        items = json.loads(raw_items)
    except Exception as e:
        print("JSON ERROR:", e)
        items = []

    user_root = os.path.join(
        "uploads",
        session["username"]
    )

    trash_dir = os.path.join(
        user_root,
        ".trash"
    )

    os.makedirs(trash_dir, exist_ok=True)

    for item_name in items:

        source = os.path.join(
            user_root,
            current_path,
            item_name
        )

        destination = os.path.join(
            trash_dir,
            item_name
        )

        counter = 1

        while os.path.exists(destination):

            destination = os.path.join(
                trash_dir,
                f"{counter}_{item_name}"
            )

            counter += 1

        if os.path.exists(source):
            shutil.move(
                source,
                destination
            )

    return redirect(
        url_for(
            "dashboard",
            path=current_path
        )
    )

# =====================================================
# Przenoszenie poniedzy folderami
# ====================================================

@app.route("/move", methods=["POST"])
def move():

    if "username" not in session:
        return redirect(url_for("home"))

    current_path = request.form.get("current_path", "")
    item_name = request.form.get("item_name")
    target_folder = request.form.get("target_folder", "").strip()

    if not item_name or not target_folder:
        return redirect(url_for("dashboard", path=current_path))

    user_root = os.path.join("uploads", session["username"])

    source = os.path.join(user_root, current_path, item_name)
    destination_dir = os.path.join(user_root, target_folder)

    if os.path.exists(source) and os.path.isdir(destination_dir):
        shutil.move(
            source,
            os.path.join(destination_dir, item_name)
        )

    return redirect(url_for("dashboard", path=current_path))
 
# =====================================================
# DASHBOARD
# =====================================================

@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect(url_for("home"))

    current_path = request.args.get("path", "")
    user_root = os.path.join("uploads", session["username"])
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
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT storage_limit FROM users WHERE username = ?", (session["username"],))
    result = c.fetchone()
    conn.close()

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
# Upload
# =====================================================

@app.route("/upload", methods=["POST"])
def upload():
    if "username" not in session:
        return redirect(url_for("home"))

    username = session["username"]
    current_path = request.form.get("current_path", "")
    files = request.files.getlist("file")
    import json

    relative_paths = request.form.get("relative_paths", "[]")
    print("RELATIVE_PATHS_RAW:", relative_paths)

    try:
        relative_paths = json.loads(relative_paths)
        print("RELATIVE_PATHS:", relative_paths)
        print("FILES_COUNT:", len(files))
    except:
        relative_paths = []
    if not files or files[0].filename == "":
        return redirect(url_for("dashboard", path=current_path))

    # 1. Przygotuj ścieżki
    user_root = get_user_base_folder(username) # korzystamy z Twojej funkcji pomocniczej
    save_path = os.path.normpath(os.path.join(user_root, current_path))
    os.makedirs(save_path, exist_ok=True)

    # 2. Pobierz limit użytkownika z bazy
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT storage_limit FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()

    if not result:
        flash("Błąd użytkownika")
        return redirect(url_for("dashboard", path=current_path))

    storage_limit_mb = result[0]
    
    # 3. Policz aktualnie zajęte miejsce (w bajtach)
    current_usage_bytes = get_folder_size(user_root)

    # 4. Przetwórz każdy plik
    for file in files:
        print("UPLOAD:", repr(file.filename))
        if file and file.filename != "":
        
            if len(relative_paths) > 0 and files.index(file) < len(relative_paths):
                relative_name = relative_paths[files.index(file)]
            else:
                relative_name = file.filename

            relative_name = relative_name.replace("\\", "/")

            filename = os.path.basename(relative_name)

            target_dir = os.path.join(
                save_path,
                os.path.dirname(relative_name)
            )

            os.makedirs(target_dir, exist_ok=True)
            
            # Sprawdź rozmiar nowego pliku
            file.seek(0, os.SEEK_END)
            file_size_bytes = file.tell()
            file.seek(0)

            # Sprawdź czy nie przekroczy limitu (przeliczamy bajty na MB)
            if (current_usage_bytes + file_size_bytes) / (1024 * 1024) > storage_limit_mb:
                flash(f"Błąd: Plik {filename} przekroczyłby Twój limit miejsca!")
                continue # Pomiń ten plik i idź do następnego

            # 5. Zapisz plik
            file_path = os.path.join(target_dir, filename)

            if filename.strip() == "":
                continue

            if "." not in filename:
                os.makedirs(file_path, exist_ok=True)
                continue
            # Wersjonowanie
            if os.path.exists(file_path):

                from datetime import datetime

                versions_dir = os.path.join(
                    user_root,
                    ".versions"
                )

                os.makedirs(versions_dir, exist_ok=True)

                timestamp = datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                )

                version_file = os.path.join(
                    versions_dir,
                    f"{filename}_{timestamp}"
                )

                shutil.copy2(
                    file_path,
                    version_file
                )            

            file.save(file_path)
           
            # Automatyczne rozpakowanie ZIP
            if filename.lower().endswith(".zip"):
                try:
                    import zipfile

                    with zipfile.ZipFile(file_path, "r") as zip_ref:
                        for member in zip_ref.infolist():

                            if member.filename.startswith("__MACOSX/"):
                                continue

                            try:
                                fixed_name = member.filename.encode("cp437").decode("utf-8")
                            except:
                                fixed_name = member.filename

                            target = os.path.join(save_path, fixed_name)

                            if member.is_dir():
                                os.makedirs(target, exist_ok=True)
                            else:
                                os.makedirs(os.path.dirname(target), exist_ok=True)

                                with zip_ref.open(member) as src:
                                    with open(target, "wb") as dst:
                                        shutil.copyfileobj(src, dst)

                    os.remove(file_path)

                except Exception as e:
                    print("BŁĄD ZIP:", e)
                    flash(f"Błąd rozpakowania ZIP: {e}")
          
            # Aktualizuj licznik zajętego miejsca dla kolejnych plików w tej samej pętli
            current_usage_bytes += file_size_bytes

            # 6. Generuj miniaturkę (tylko dla obrazów)
            ext = filename.rsplit('.', 1)[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif']:
                generate_thumb(file_path)

    return redirect(url_for("dashboard", path=current_path))


# =====================================================
# ADMIN
# =====================================================

@app.route("/admin")
def admin_panel():
    if not is_logged_in() or not is_admin():
        abort(403)

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, username, role, storage_limit FROM users")
    users = c.fetchall()
    conn.close()

    return render_template(
        "admin.html",
        users=users,
        total_users=len(users)
    )

# =====================================================
# ADMIN ZMIANA POJEMNOSCI DYSKU
# =====================================================

@app.route("/admin/update_limit/<int:user_id>", methods=["POST"])
def update_limit(user_id):
    if not is_logged_in() or not is_admin():
        abort(403)

    try:
        new_limit = float(request.form.get("storage_limit"))
        if new_limit <= 0:
            new_limit = 100
    except:
        new_limit = 100

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE users SET storage_limit = ? WHERE id = ?", (new_limit, user_id))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_panel"))

# =====================================================
# DODAJ UŻYTKOWNIKA
# =====================================================

@app.route("/admin/add_user", methods=["POST"])
def add_user():
    if not is_logged_in() or not is_admin():
        abort(403)

    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role", "user")

    if not username or not password:
        flash("Brak danych do utworzenia użytkownika", "error")
        return redirect(url_for("admin_panel"))

    hashed_password = generate_password_hash(password)

    try:
        storage_limit = float(request.form.get("storage_limit", 100))
        if storage_limit <= 0:
            storage_limit = 100
    except:
        storage_limit = 100

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    try:
        c.execute("""
            INSERT INTO users (username, password, role, storage_limit)
            VALUES (?, ?, ?, ?)
        """, (username, hashed_password, role, storage_limit))

        conn.commit()
        conn.close()

        os.makedirs(os.path.join(UPLOAD_FOLDER, username), exist_ok=True)

        flash(f"Użytkownik {username} został utworzony", "success")

    except sqlite3.IntegrityError:
        conn.close()
        flash("Użytkownik już istnieje", "error")

    return redirect(url_for("admin_panel"))

# =====================================================
# USUWANIE UŻYTKOWNIKA
# =====================================================

@app.route("/admin/delete_user", methods=["POST"])
def delete_user():
    if not is_logged_in() or not is_admin():
        abort(403)

    username = request.form.get("username")

    if not username:
        return "Brak użytkownika", 400

    if username == session.get("username"):
        return "Nie możesz usunąć samego siebie", 400

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = c.fetchone()

    if not user:
        conn.close()
        return "Użytkownik nie istnieje", 404

    c.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()

    user_folder = os.path.join(UPLOAD_FOLDER, username)
    if os.path.exists(user_folder):
        shutil.rmtree(user_folder)

    return redirect(url_for("admin_panel"))

# =====================================================
# Lista wersji pliku
# =====================================================

@app.route("/versions")
def show_versions():

    if "username" not in session:
        return redirect(url_for("home"))

    filename = request.args.get("name")

    user_root = os.path.join("uploads", session["username"])
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
