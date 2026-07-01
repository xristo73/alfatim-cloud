from flask import (
    session,
    request,
    redirect,
    url_for
)

import os
import shutil

from utils.paths import get_user_base_folder
from werkzeug.utils import secure_filename


def create_folder():
    folder_name = secure_filename(request.form.get("folder_name"))
    current_path = request.form.get("current_path", "")

    user_root = get_user_base_folder(session["username"])
    new_folder = os.path.join(user_root, current_path, folder_name)

    os.makedirs(new_folder, exist_ok=True)

    return redirect(url_for("dashboard.dashboard", path=current_path))
