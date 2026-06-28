from flask import Blueprint

sharing_bp = Blueprint("sharing", __name__)

from flask import (
    Blueprint,
    session,
    request,
    redirect,
    url_for,
    flash,
    abort,
    send_from_directory
)

import os
import secrets

from database import get_db

sharing_bp = Blueprint("sharing", __name__)


@sharing_bp.route("/share_create")
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

    db = get_db()
    c = db.cursor()

    c.execute(
        "INSERT INTO shared_links (token, filepath) VALUES (?, ?)",
        (token, filepath)
    )

    db.commit()

    flash(
        f"https://chmura.alfatim.pl/share/{token}",
        "success"
    )

    return redirect(url_for("dashboard", path=current_path))


@sharing_bp.route("/share/<token>")
def share_file(token):

    db = get_db()
    c = db.cursor()

    c.execute(
        "SELECT filepath FROM shared_links WHERE token=?",
        (token,)
    )

    result = c.fetchone()

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
