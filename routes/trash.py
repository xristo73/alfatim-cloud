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

    return redirect(url_for("dashboard", path=".trash"))
