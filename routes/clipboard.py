from utils.paths import get_user_base_folder
from flask import (
    Blueprint,
    session,
    request,
    redirect,
    url_for
)

import os
import shutil
import json

from utils.paths import get_user_base_folder
from flask import current_app

clipboard_bp = Blueprint("clipboard", __name__)

@clipboard_bp.route("/clipboard_copy", methods=["POST"])
def clipboard_copy():

    if "username" not in session:
        return redirect(url_for("auth.home"))

    import json

    session["clipboard"] = {
        "action": "copy",
        "current_path": request.form.get("current_path", ""),
        "items": json.loads(
            request.form.get("items", "[]")
        )
    }
    print("CLIPBOARD SAVE:", session["clipboard"])
    print("CLIPBOARD:", session["clipboard"])
    print("SESSION:", dict(session))
    return "OK"

@clipboard_bp.route("/clipboard_paste", methods=["POST"])
def clipboard_paste():

    if "username" not in session:
        return redirect(url_for("auth.home"))

    clipboard = session.get("clipboard")
    print("PASTE:", clipboard)
    print("CLIPBOARD:", clipboard)
    print("TARGET:", request.form.get("current_path", ""))

    if not clipboard:
        return redirect(url_for("dashboard.dashboard"))

    user_root = get_user_base_folder(session["username"])

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

@clipboard_bp.route("/bulk_copy", methods=["POST"])
def bulk_copy():

    if "username" not in session:
        return redirect(url_for("auth.home"))

    import json

    current_path = request.form.get("current_path", "")
    target_folder = request.form.get("target_folder", "")

    items = json.loads(
        request.form.get("items", "[]")
    )

    user_root = get_user_base_folder(session["username"])

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


