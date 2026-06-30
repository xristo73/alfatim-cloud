from flask import Blueprint, request, session, redirect, url_for, flash
from utils.decorators import login_required
from database import get_db
from utils.paths import get_user_base_folder
from utils.helpers import get_folder_size, generate_thumb

import os
import shutil

upload_bp = Blueprint("upload", __name__)

@upload_bp.route("/upload", methods=["POST"])
@login_required
def upload():

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
    db = get_db()
    c = db.cursor()
    c.execute(
        "SELECT storage_limit FROM users WHERE username = ?",
        (username,)
    )
    result = c.fetchone()

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
