"""
Commands for observe web app.
"""
import os

from flask import Blueprint, render_template, request
from werkzeug.utils import secure_filename

import azcam
from .queue import Queue

# create queue tool
queue = Queue()

# create Flask Blueprint
queue_bp = Blueprint(
    "queue",
    __name__,
    static_folder="/azcam/azcam-queue/azcam_queue/static_queue",
    template_folder="",
)


def load_queue():
    if azcam.db.get("webserver") is not None:
        azcam.db.webserver.app.register_blueprint(queue_bp)
        azcam.log("Loaded queue")

    return


@queue_bp.route("/queue", defaults={"page": "queue"}, methods=["GET"])
def show_queue(page):
    table_data = [
        list(range(17)),
    ]
    return render_template(f"{page}.html", table_data=table_data)


@queue_bp.route("/queue_test", methods=["POST", "GET"])
def queue_test():

    url = request.url
    print(url)
    print(request.query_string)

    email = request.args.get("email")
    return f"hi {email}"


@queue_bp.route("/queue/upload", methods=["POST"])
def script_upload():
    url = request.url
    print("UPLOAD:", url)
    azcam.log(url, prefix="Web-> ")
    f = request.files["file"]
    f.save(
        os.path.join(
            azcam.db.webserver.app.config["UPLOAD_FOLDER"], secure_filename(f.filename)
        )
    )
    return "OK"
