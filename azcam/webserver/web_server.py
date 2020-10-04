"""
Configure and start Flask web server application.

Import this after all configuration has been completed.
"""

import sys
import os
import threading
import logging
from urllib.parse import urlparse

from flask import Flask, jsonify, request, render_template, send_from_directory
from werkzeug.utils import secure_filename

import azcam


# url= "http://locahost:2402/api/instrument/set_filter?filter=1&filter_id=2"


class WebServer(object):
    """
    AzCam web server.
    """

    def __init__(self):

        # create flask app
        app = Flask(__name__, template_folder="")
        self.app = app

        self.logcommands = 1

        self.mock_mode = 0

        # define pages
        index_home = "index.html"
        updates_home = "updates.html"
        status_home = "status.html"
        exptool_home = "exptool.html"
        observe_home = "webobs.html"

        #: port for webserver
        self.webport = azcam.api.cmdserver.port + 1

        azcam.api.webserver = self

        self.upload_folder = "/data/uploads"

        self.is_running = 0

        # ******************************************************************************
        # home pages
        # ******************************************************************************
        @app.route("/", methods=["GET"])
        def index():
            return render_template(index_home)

        @app.route("/updates", methods=["GET"])
        def updates():
            return render_template(updates_home)

        @app.route("/status", methods=["GET"])
        def status():
            return render_template(status_home)

        @app.route("/exptool", methods=["GET"])
        def exptool():
            return render_template(exptool_home)

        @app.route("/webobs", methods=["GET"])
        def webobs():
            table_data = [
                list(range(17)),
            ]
            return render_template(observe_home, table_data=table_data)

        @app.route("/favicon.ico")
        def favicon():
            return send_from_directory(
                os.path.join(app.root_path, "static"),
                "favicon.ico",
                mimetype="image/vnd.microsoft.icon",
            )

        # ******************************************************************************
        # API commands - .../api//object/command
        # ******************************************************************************
        @app.route("/api/<path:command>", methods=["GET"])
        def api(command):
            """
            Remote web api commands. such as: /api/expose or /api/exposure/reset
            """

            url = request.url
            if self.logcommands:
                if "api/exposure/get_status" in url or "api/webobs/watchdog" in url:
                    pass
                else:
                    azcam.log(url, prefix="Web-> ")
            if self.mock_mode:
                reply = "mock data"
            else:
                reply = self.webcommand(url)
                if self.logcommands:
                    if "api/exposure/get_status" in url or "api/webobs/watchdog" in url:
                        pass
                else:
                    azcam.log(reply, prefix="Web->   ")
            return self.make_response(command, reply)

        @app.route("/api/webobs/upload", methods=["POST"])
        def upload_file():
            url = request.url
            if self.logcommands:
                azcam.log(url, prefix="Web-> ")
            f = request.files["file"]
            f.save(
                os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(f.filename))
            )
            return self.make_response("upload file", "file uploaded successfully")

    def webcommand(self, url):
        """
        Parse a web URL and make call to proper object method, returning reply.
        """

        try:
            caller, kwargs = self.webparse(url)
            reply = caller() if kwargs is None else caller(**kwargs)

        except azcam.AzcamError as e:
            azcam.log(f"webcommand error: {e}")
            if e.error_code == 4:
                reply = "remote call not allowed"
            else:
                reply = f"webcommand error: {repr(e)}"
        except Exception as e:
            azcam.log(e)
            reply = f"invalid API command: {url}"

        return reply

    def webparse(self, url):
        """
        Parse URL.
        """

        s = urlparse(url)
        p = s.path[5:]  # remove /api/
        # p = s.path[1:]

        try:
            tokens = p.split("/")
        except Exception as e:
            raise e("Invalid API command")

        obj, method = tokens[:2]
        args = s.query.split("&")

        if args == [""]:
            kwargs = None
        else:
            kwargs = {}
            for arg1 in args:
                arg, par = arg1.split("=")
                kwargs[arg] = par

        # security check
        if obj not in azcam.db.cmd_objects:
            raise azcam.AzcamError(f"remote call not allowed: {obj}", 4)

        caller = getattr(azcam.db.cmd_objects[obj], method)

        return caller, kwargs

    def make_response(self, command, reply):

        # generic response
        response = {
            "message": "Finished",
            "command": command,
            "data": reply,
        }

        response = jsonify(response)

        return response

    def stop(self):
        """
        Stops command server running in thread.
        """

        azcam.log("Stopping the webserver is not supported")

        return

    def start(self):
        """
        Start web server.
        """

        azcam.log(f"Starting webserver - listening on port {self.webport}")

        # turn off development server warning
        cli = sys.modules["flask.cli"]
        cli.show_server_banner = lambda *x: None

        if 1:
            log1 = logging.getLogger("werkzeug")
            log1.setLevel(logging.ERROR)

        # 0 => threaded for command line use (when imported)
        if 0:
            self.app.jinja_env.auto_reload = True
            self.app.config["TEMPLATES_AUTO_RELOAD"] = True
            self.app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
            self.app.config["UPLOAD_FOLDER"] = self.upload_folder
            self.app.run(debug=True, threaded=False, host="0.0.0.0", port=self.webport)
        else:
            self.app.jinja_env.auto_reload = True
            self.app.config["TEMPLATES_AUTO_RELOAD"] = True
            self.app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
            self.app.config["UPLOAD_FOLDER"] = self.upload_folder
            self.webthread = threading.Thread(
                target=self.app.run,
                kwargs={"threaded": True, "host": "0.0.0.0", "port": self.webport},
            )
            self.webthread.daemon = True  # terminates wehn main process exits
            self.webthread.start()
            self.is_running = 1

        return
