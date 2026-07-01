from flask import Blueprint, render_template, request, session
from utils.decorators import login_required
from utils.paths import get_user_base_folder
import os

search_bp = Blueprint("search", __name__)


@search_bp.route("/search")
@login_required
def search():

    query = request.args.get("q", "").lower()

    user_root = get_user_base_folder(session["username"])

    results = []

    for root, dirs, files in os.walk(user_root):

        for folder in dirs:
            if query in folder.lower():
                rel_path = os.path.relpath(
                    os.path.join(root, folder),
                    user_root
                )

                results.append({
                    "name": folder,
                    "path": rel_path,
                    "is_folder": True
                })

        for file in files:
            if query in file.lower():

                rel_path = os.path.relpath(
                    os.path.join(root, file),
                    user_root
                )

                results.append({
                    "name": file,
                    "path": rel_path,
                    "is_folder": False
                })

    return render_template(
        "search.html",
        results=results,
        query=query
    )
