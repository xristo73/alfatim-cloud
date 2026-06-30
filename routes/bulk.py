from flask import Blueprint, session, request, redirect, url_for, send_file, current_app
from utils.decorators import login_required
from utils.paths import get_user_base_folder

import os
import shutil

bulk_bp = Blueprint("bulk", __name__)


@bulk_bp.route("/bulk_zip", methods=["POST"])
def bulk_zip():

    current_app.logger.error("BULK ZIP CALLED")
    current_path = request.form.get("current_path", "")

    if "username" not in session:
        return redirect(url_for("home"))

    import json
    import tempfile
    import zipfile

    current_path = request.form.get("current_path", "")

    items = json.loads(
        request.form.get("items", "[]")
    )

    user_root = os.path.join(
        "uploads",
        session["username"]
    )

    temp_zip = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".zip"
    )

    with zipfile.ZipFile(
        temp_zip.name,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zipf:

        for item_name in items:

            item_path = os.path.join(
                user_root,
                current_path,
                item_name
            )

            if os.path.isfile(item_path):

                zipf.write(
                    item_path,
                    arcname=item_name
                )

            elif os.path.isdir(item_path):

                for root, dirs, files in os.walk(item_path):

                    for file in files:

                        full_path = os.path.join(
                            root,
                            file
                        )

                        arcname = os.path.relpath(
                            full_path,
                            os.path.join(
                                user_root,
                                current_path
                            )
                        )

                        zipf.write(
                            full_path,
                            arcname=arcname
                        )

    current_app.logger.error(f"ZIP FILE: {temp_zip.name}")
    current_app.logger.error(f"ZIP EXISTS: {os.path.exists(temp_zip.name)}")
    current_app.logger.error(f"ZIP SIZE: {os.path.getsize(temp_zip.name)}") 

    return send_file(
        temp_zip.name,
        mimetype="application/zip",
        as_attachment=True,
        download_name="pobrane.zip"
    )

@bulk_bp.route("/bulk_delete", methods=["POST"])
def bulk_delete():

    if "username" not in session:
        return redirect(url_for("home"))

    print("=== BULK DELETE ===")
    print(request.form)
    print(request.form.get("items"))


    import json

    current_path = request.form.get(
        "current_path",
        ""
    )
    
    raw_items = request.form.get("items", "")

    print("ITEMS_RAW:", repr(raw_items))

    try:
        items = json.loads(raw_items)
    except Exception as e:
        print("JSON ERROR:", e)
        items = []

    user_root = os.path.join(
        "uploads",
        session["username"]
    )

    trash_dir = os.path.join(
        user_root,
        ".trash"
    )

    os.makedirs(trash_dir, exist_ok=True)

    for item_name in items:

        source = os.path.join(
            user_root,
            current_path,
            item_name
        )

        destination = os.path.join(
            trash_dir,
            item_name
        )

        counter = 1

        while os.path.exists(destination):

            destination = os.path.join(
                trash_dir,
                f"{counter}_{item_name}"
            )

            counter += 1

        if os.path.exists(source):
            shutil.move(
                source,
                destination
            )

    return redirect(
        url_for(
            "dashboard",
            path=current_path
        )
    )


@bulk_bp.route("/bulk_move", methods=["POST"])
def bulk_move():

    current_app.logger.error("=== MOVE ===")
    current_app.logger.error(request.form)
    current_app.logger.error("item_name = %s", request.form.get("item_name"))
    current_app.logger.error("target_folder = %s", request.form.get("target_folder"))
    current_app.logger.error("current_path = %s", request.form.get("current_path"))

    if "username" not in session:
        return redirect(url_for("home"))

    import json
    target_folder = request.form.get("target_folder", "")
    current_path = request.form.get("current_path", "")

    items = json.loads(
        request.form.get("items", "[]")
    )

    user_root = os.path.join(
        "uploads",
        session["username"]
    )

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

        if os.path.exists(source):
            shutil.move(
                source,
                destination
            )

    return redirect(
        url_for(
            "dashboard",
            path=current_path
        )
    )
