from flask import Blueprint, session, request, redirect, url_for
from utils.decorators import login_required
from utils.paths import get_user_base_folder

import os
import shutil
from datetime import datetime

versions_bp = Blueprint("versions", __name__)

@versions_bp.route("/versions")
def show_versions():

    if "username" not in session:
        return redirect(url_for("auth.home"))

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
            <a href="{url_for('versions.restore_version', name=filename, version=v)}">
                [Przywróć]
            </a>
        </p>
        """

    html += '<br><a href="/dashboard">Powrót</a>'

    return html

@versions_bp.route("/restore_version")
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

    return redirect(url_for("dashboard.dashboard"))
