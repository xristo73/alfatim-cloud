from flask import (
    Blueprint,
    session,
    redirect,
    url_for,
    request
)

import os
import shutil

from utils.decorators import login_required
from utils.paths import get_user_base_folder


trash_bp = Blueprint(
    "trash",
    __name__
)

@trash_bp.route("/restore")
@login_required
def restore():

    item_name = request.args.get("name")

    user_root = get_user_base_folder(session["username"])

    source = os.path.join(user_root, ".trash", item_name)
    destination = os.path.join(user_root, item_name)

    if os.path.exists(source):
        shutil.move(source, destination)

    return redirect(url_for("dashboard.dashboard", path=".trash"))



@trash_bp.route("/empty_trash", methods=["POST"])
@login_required
def empty_trash():

    user_root = get_user_base_folder(session["username"])
    trash_dir = os.path.join(user_root, ".trash")

    if os.path.isdir(trash_dir):

        for item in os.listdir(trash_dir):

            path = os.path.join(trash_dir, item)

            if os.path.isdir(path):
                shutil.rmtree(path)

            else:
                os.remove(path)

    return redirect(url_for("dashboard.dashboard", path=".trash"))
