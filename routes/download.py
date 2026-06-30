from flask import Blueprint, session, request, send_from_directory
from utils.decorators import login_required
from utils.paths import get_user_base_folder
import os

download_bp = Blueprint("download", __name__)


@download_bp.route("/file/<path:filepath>")
@login_required
def serve_file(filepath):

    user_root = get_user_base_folder(session["username"])

    folder = os.path.dirname(filepath)
    filename = os.path.basename(filepath)

    return send_from_directory(
        os.path.join(user_root, folder),
        filename
    )


@download_bp.route("/download/<path:filepath>")
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


@download_bp.route("/download")
@login_required
def download_file():

    current_path = request.args.get("path", "")
    filename = request.args.get("name")

    user_root = get_user_base_folder(session["username"])
    folder = os.path.join(user_root, current_path)

    return send_from_directory(
        folder,
        filename,
        as_attachment=True
    )
