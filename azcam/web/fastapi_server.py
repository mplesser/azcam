"""
Configure and start fastapi application using uvicorn.
Import this after all configuration has been completed.
All API commands suported here must start with ""http://locahost:xxxx/api/" where xxxx is the
port number like 2402.

Query string example: "http://localhost:2402/api/set_filter?filter=1&filter_id=2"

JSON example:
    data = {
        "command": "set_par",
        "args": [],
        "kwargs": {"parameter": "imagetest", "value": 3333},
    }
    r = requests.post("http://localhost:2403/api", json=data1)
    print(r.status_code, r.json())
    
Default response is JSON:
    response = {
        "message": "Finished",
        "command": urlparse(url).path,
        "data": reply,
    }

"""

import os
import threading

import uvicorn
from fastapi import FastAPI, Request, APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.wsgi import WSGIMiddleware

from azcam.web.exposure.exposure_web import ExposureWeb
from azcam.web.queue.queue_web import QueueWeb
from azcam.web.status.status_web import StatusWeb


import azcam
from azcam import exceptions


class WebServer(object):
    """
    Azcam web server.
    """

    def __init__(self):
        self.templates_folder = ""
        self.index = "index.html"
        self.favicon_path = None

        self.logcommands = 0
        self.logstatus = 0
        self.message = ""  # customized message
        self.datafolder = None

        # port for webserver
        self.port = None

        self.is_running = 0

        azcam.db.webserver = self

    def initialize(self):
        """
        Initialize application.
        """

        # create app
        app = FastAPI()
        self.app = app

        if self.datafolder is None:
            self.datafolder = os.path.dirname(__file__)

        if self.favicon_path is None:
            self.favicon_path = os.path.join(os.path.dirname(__file__), "favicon.ico")

        self.index = os.path.join(os.path.dirname(__file__), self.index)
        self.version = 1  # API version

        expweb = ExposureWeb()
        expweb.logcommands = 1
        expweb.logstatus = 0
        queueweb = QueueWeb()
        queueweb.logcommands = 1
        queueweb.logstatus = 0
        statusweb = StatusWeb()
        statusweb.initialize()

        app.mount("/exposure", WSGIMiddleware(expweb.app.server))
        app.mount("/queue", WSGIMiddleware(queueweb.app.server))

        # templates folder
        try:
            templates = Jinja2Templates(directory=os.path.dirname(self.index))
        except Exception:
            pass

        # ******************************************************************************
        # Home - /
        # ******************************************************************************
        @app.get("/", response_class=HTMLResponse)
        def home(request: Request):
            index = os.path.basename(self.index)
            return templates.TemplateResponse(
                index,
                {
                    "request": request,
                    "message": self.message,
                    "webport": azcam.db.cmdserver.port + 1,
                },
            )

        # ******************************************************************************
        # Set API version: /api/set_version?version=2
        # ******************************************************************************
        @app.get("/api/set_version", response_class=JSONResponse)
        async def set_version(request: Request, command: str = None):

            qpars = request.query_params
            self.version = int(qpars["version"])

            response = {
                "message": "Finished",
                "command": f"api.set_version",
                "data": self.version,
            }

            return JSONResponse(response)

        # ******************************************************************************
        # Example of a special case: /api/exposure/get_status
        # ******************************************************************************
        @app.get("/api/exposure/get_status", response_class=JSONResponse)
        async def expstatus(request: Request, command: str = None):

            expstatus = azcam.db.api.get_status()

            response = {
                "message": "Finished",
                "command": f"exposure.get_status",
                "data": expstatus,
            }

            return JSONResponse(response)

        @app.get("/favicon.ico", include_in_schema=False)
        async def favicon():
            return FileResponse(self.favicon_path)

        # ******************************************************************************
        # API interface - ../api/command or ../api JSON
        # ******************************************************************************

        @app.post("/api", response_class=JSONResponse)
        @app.get("/api/{command:path}", response_class=JSONResponse)
        async def api(request: Request, command: str = None):
            """
            Remote web api commands.
            """

            if self.version == 1 or self.version == 2:

                # JSON
                if command is None:
                    args = await request.json()
                    try:
                        toolid = azcam.db.api
                        command = getattr(toolid, args["command"])

                        arglist = args["args"]
                        kwargs = args["kwargs"]
                        reply = command(*arglist, **kwargs)
                    except Exception as e:
                        reply = repr(e)
                        azcam.log(e)

                    response = {
                        "message": "Finished",
                        "command": f"api.{args['command']}",
                        "data": reply,
                    }

                    return JSONResponse(response)

                # query string
                url = command
                qpars = request.query_params

                if self.logcommands:
                    azcam.log(url, prefix="Web-> ")

                reply = self.web_command(url, qpars)

                if self.logcommands:
                    azcam.log(reply, prefix="---->   ")

                return JSONResponse(reply)

            else:

                # query string
                url = command
                qpars = request.query_params

                response = {
                    "message": "Finished",
                    "command": url,
                    "data": "Invalid API version",
                }

                return JSONResponse(response)

    # ******************************************************************************
    # webserver methods
    # ******************************************************************************

    def add_router(self, router):
        """
        Add router.
        """

        self.app.include_router(router)

        return

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

        self.initialize()

        if self.port is None:
            self.port = azcam.db.cmdserver.port + 1

        azcam.log(f"Starting webserver - listening on port {self.port}")

        # uvicorn.run(self.app)

        arglist = [self.app]
        kwargs = {"port": self.port, "host": "0.0.0.0", "log_level": "critical"}

        thread = threading.Thread(
            target=uvicorn.run, name="uvicorn", args=arglist, kwargs=kwargs
        )
        thread.daemon = True  # terminates when main process exits
        thread.start()

        self.is_running = 1

        return

    def web_command(self, url, qpars=None):
        """
        Parse and execute a command string received as a URL.
        Returns the reply as a JSON packet.
        """

        try:
            method = url
            kwargs = qpars._dict

            caller = getattr(azcam.db.api, method)
            reply = caller() if kwargs is None else caller(**kwargs)

        except Exception as e:
            azcam.log(e)
            reply = f"invalid API command: {url}"

        # generic response
        response = {
            "message": "Finished",
            "command": url,
            "data": reply,
        }

        return response
