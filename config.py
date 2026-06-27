import os
import secrets
import config

# ==========================================
# ŚCIEŻKI
# ==========================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATABASE = os.path.join(BASE_DIR, "users.db")

# ==========================================
# FLASK
# ==========================================

SECRET_KEY = "2ec108687d46ec451fbc7142c651e1fb568d4b6b64aca6200e7b652f703feed2"

MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB

# ==========================================
# PLIKI
# ==========================================

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "pdf",
    "txt",
    "doc",
    "docx",
    "xlsx",
    "zip",
}

# ==========================================
# INICJALIZACJA
# ==========================================

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==========================================
# ŚCIEŻKI
# ==========================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATABASE = os.path.join(BASE_DIR, "users.db")

# ==========================================
# FLASK
# ==========================================

SECRET_KEY = "2ec108687d46ec451fbc7142c651e1fb568d4b6b64aca6200e7b652f703feed2"

MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB

# ==========================================
# PLIKI
# ==========================================

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "pdf",
    "txt",
    "doc",
    "docx",
    "xlsx",
    "zip",
}

# ==========================================
# INICJALIZACJA
# ==========================================

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
