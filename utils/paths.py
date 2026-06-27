import os
from flask import abort
import config


def get_user_base_folder(username):
    path = os.path.join(config.UPLOAD_FOLDER, username)
    os.makedirs(path, exist_ok=True)
    return path


def secure_user_path(username, subpath=""):
    base = get_user_base_folder(username)
    full_path = os.path.normpath(os.path.join(base, subpath))

    if not full_path.startswith(base):
        abort(403)

    return full_path
