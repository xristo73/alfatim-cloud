
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
from routes.dashboard import dashboard_bp
from routes.share import share_bp
from routes.auth import auth_bp
from routes.versions import versions_bp
from routes.search import search_bp
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
app.register_blueprint(dashboard_bp)
app.register_blueprint(share_bp)
app.register_blueprint(versions_bp)
app.register_blueprint(search_bp)
UPLOAD_FOLDER = config.UPLOAD_FOLDER
DATABASE = config.DATABASE
ALLOWED_EXTENSIONS = config.ALLOWED_EXTENSIONS

init_db()


# =====================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
