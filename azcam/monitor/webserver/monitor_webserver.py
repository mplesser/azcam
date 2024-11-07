"""
Configure and start azcammonitor web server.
"""

import socket
import os
import time
import threading
from urllib.parse import urlparse

import uvicorn
from fastapi import FastAPI, Request, APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import azcam
import azcam.utils
import azcam.exceptions

"""
Home page:
http://locahost:2400/

API:
.../api/start_process?name=vatt4k (e.g. vatt4k, vattspec, mont4k-rts2, 90prime, bcspec)
.../api/start_process?cmd_port=2402
"""


class WebServer(object):
    """
    Monitor-azcam web server.
    """

    def __init__(self):
        # create app
        app = FastAPI()
        self.app = app

        app.mount("/static", StaticFiles(directory="."), name="static")

        self.logcommands = 0

        # define pages
        self.index_home = "index.html"

        # port for webserver
        self.webport = 2400

        self.is_running = 0

        self.message = "Welcome to azcammonitor Home"

        self.favicon_path = ""

        self.hostname = socket.gethostname()

        # templates folder
        dd = azcam.utils.fix_path(os.path.dirname(__file__))

        static_path = os.path.join(dd, "static")

        templates = Jinja2Templates(directory=dd)
        self.favicon_path = os.path.join(static_path, "favicon.ico")
        self.javascript_path = os.path.join(static_path, "monitor.js")
        self.style_path = os.path.join(static_path, "style.css")

        # ******************************************************************************
        # home page
        # ******************************************************************************
        @app.get("/", response_class=HTMLResponse)
        def home(request: Request):
            azcam.db.monitor.get_ids()
            return templates.TemplateResponse(
                os.path.basename(self.index_home),
                {
                    "request": request,
                    "process_list": azcam.db.monitor.process_list,
                    "machine_id": self.hostname,
                },
            )

        # ******************************************************************************
        # api commands
        # ******************************************************************************
        # @app.route("/api/<path:command>", methods=["GET"])
        @app.get("/api/{command:path}", response_class=JSONResponse)
        def api(request: Request, command: str = None):
            """
            Remote web commands such as: /exposure/reset
            """

            # query string
            qpars = request.query_params

            if self.logcommands:
                print("Web->", command, qpars)

            reply = self.web_command(command, qpars)

            if self.logcommands:
                print("Web->   ", reply["data"])

            return JSONResponse(reply)

        @app.get("/favicon.ico", include_in_schema=False)
        async def favicon():
            return FileResponse(self.favicon_path)

        @app.get("/monitor.js", include_in_schema=False)
        async def monitor():
            return FileResponse(self.javascript_path)

        @app.get("/style.css", include_in_schema=False)
        async def style():
            return FileResponse(self.style_path)

    def web_command(self, command, qpars):
        """
        Parse and execute a command string.
        Returns the reply as dictionary.
        """

        kwargs = qpars._dict

        try:
            caller = getattr(azcam.db.monitor, command)
            reply = caller(**kwargs)

        except azcam.exceptions.AzcamError as e:
            print(f"web_command error: {e}")
            if e.error_code == 4:
                reply = "remote call not allowed"
            else:
                reply = f"web_command error: {repr(e)}"
        except Exception as e:
            print(e)
            reply = f"API command error: {command}"

        # generic response
        response = {
            "message": "Finished",
            "command": command,
            "args": kwargs,
            "data": reply,
        }

        return response

    def parse(self, url, qpars=None):
        """
        Parse URL.
        Return the caller object, method, and keyword arguments.
        Object may be compound, like "exposure.image.focalplane".

        URL example: http://locahost:2403/api/instrument/set_filter?filter=1&filter_id=2
        """

        # parse URL
        p = url

        try:
            tokens = p.split("/")
        except Exception as e:
            raise e("API command error - parse split")

        # get oject and method
        if len(tokens) != 2:
            raise azcam.exceptions.AzcamError("API command error - parse length")
        obj, method = tokens

        # get arguments
        kwargs = qpars._dict

        return obj, method, kwargs

    def webapi(self, command):
        """
        Parse a web URL and make call to proper object method, returning reply.
        """

        try:
            caller = self.webparse(command)
            reply = self.webcall(caller)
        except azcam.exceptions.AzcamError as e:
            if e.error_code == 4:
                reply = "remote call not allowed"
        except Exception as e:
            print(repr(e))
            reply = "ERROR executing web command"

        return reply

    def webparse(self, command):
        """
        Parse URL.
        """

        # s = urlparse(str(url))
        # p = s.path[5:]  # remove /api/
        # print(s)
        # print(p)

        # try:
        #     obj, method = p.split("/")
        # except Exception as e:
        #     raise e("API error command")

        # print(obj)

        # args = s.query.split("&")

        # if args == [""]:
        #     kwargs = None
        # else:
        #     kwargs = {}
        #     for arg1 in args:
        #         arg, par = arg1.split("=")
        #         kwargs[arg] = par

        # # security check
        # if obj != "monitor":
        #     raise azcam.exceptions.AzcamError(f"remote call not allowed: {obj}", 4)

        caller = getattr(azcam.db.monitor, command)

        return caller

    def webcall(self, caller, kwargs=None):
        """
        Make api call from webapi result.
        """

        reply = caller() if kwargs is None else caller(**kwargs)

        return reply

    def make_response(self, command, reply):
        # generic response
        response = {
            "message": "Finished",
            "command": command,
            "data": reply,
        }

        response = JSONResponse(response)

        return response

    def stop(self):
        """
        Stops command server running in thread.
        """

        print("Stopping the webserver is not supported")

        return

    def start(self):
        """
        Start web server.
        """

        # self.initialize()

        if self.webport is None:
            self.webport = 2400

        print(f"Starting azcammonitor webserver on port {self.webport}")

        if 0:
            uvicorn.run(self.app, port=2400)

        else:
            arglist = [self.app]
            kwargs = {"port": self.webport, "host": "0.0.0.0", "log_level": "critical"}

            thread = threading.Thread(
                target=uvicorn.run, name="uvicorn", args=arglist, kwargs=kwargs
            )
            thread.daemon = True  # terminates when main process exits
            thread.start()
            self.is_running = 1

        return
