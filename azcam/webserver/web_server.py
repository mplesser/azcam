"""
Configure and start Flask web server application.

Import this after all configuration has been completed.
"""

import sys
import threading
import logging
from urllib.parse import urlparse

from flask import Flask, jsonify, request, render_template

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

        #: port for webserver
        self.webport = azcam.db.cmdserver.port + 1

        azcam.db.webserver = self

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

        # ******************************************************************************
        # api commands
        # ******************************************************************************
        @app.route("/api/<path:command>", methods=["GET"])
        def api(command):
            """
            Remote web api commands. such as: /api/exposure/reset
            """

            url = request.url
            if self.logcommands:
                if "api/exposure/get_status" not in url:
                    azcam.log(url, prefix="Web-> ")
            if self.mock_mode:
                reply = "mock data"
            else:
                reply = self.webapi(url)
                if self.logcommands and "api/exposure/get_status" not in url:
                    azcam.log(reply, prefix="Web->   ")
            return self.make_response(command, reply)

    def webapi(self, url):
        """
        Parse a web URL and make call to proper object method, returning reply.
        """

        try:
            caller, kwargs = self.webparse(url)
            reply = caller() if kwargs is None else caller(**kwargs)

        except azcam.AzcamError as e:
            if e.error_code == 4:
                reply = "remote call not allowed"
            else:
                reply = f"webapi error: {repr(e)}"
        except Exception as e:
            reply = f"invalid API command: {url}"

        return reply

    def webparse(self, url):
        """
        Parse URL.
        """

        s = urlparse(url)
        p = s.path[5:]  # remove /api/

        try:
            obj, method = p.split("/")
        except Exception as e:
            raise e("Invalid API command")

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
            self.app.run(debug=True, threaded=False, host="0.0.0.0", port=self.webport)
        else:
            self.app.jinja_env.auto_reload = True
            self.app.config["TEMPLATES_AUTO_RELOAD"] = True
            self.app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
            self.webthread = threading.Thread(
                target=self.app.run,
                kwargs={"threaded": True, "host": "0.0.0.0", "port": self.webport},
            )
            self.webthread.daemon = True  # terminates wehn main process exits
            self.webthread.start()
            self.is_running = 1

        return
