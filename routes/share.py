from flask import Blueprint, send_from_directory

share_bp = Blueprint("share", __name__)

@share_bp.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory("uploads", filename)
