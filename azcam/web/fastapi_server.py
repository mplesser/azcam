"""
Configure and start fastapi application using uvicorn.
Import this after all configuration has been completed.
All API commands suported here must start with ""http://locahost:xxxx/api/" where xxxx is the
port number like 2402.

Query string example:
"http://localhost:2403/api/set_filter?filter=1&filter_id=2"

Curl example (GET):
curl -X GET http://localhost:2403/api/get_par?parameter=version

JSON example:
    data = {
        "command": "set_par",
        "args": [],
        "kwargs": {"parameter": "imagetest", "value": 1},
    }
    r = requests.post("http://localhost:2403/api", json=data1)
    print(r.status_code, r.json())

Default response is JSON:
    response = {
        "message": "Finished",
        "command": urlparse(url).path,
        "data": reply,
    }

Curl example (POST):
 curl -X POST http://localhost:2403/api -d "@json.txt"
with json.txt:
{
    "command": "get_par",
    "args": [],
    "kwargs": {"parameter": "version"}
}
"""

import os
import threading

import uvicorn
from fastapi import FastAPI, Request, APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import azcam
from azcam import exceptions


class WebServer(object):
    """
    Azcam web server.
    """

    def __init__(self):

        self.index = "index.html"
        self.favicon_path = None

        self.logcommands = 0
        self.logstatus = 0
        self.message = ""
        self.datafolder = None
        self.static_folder = None

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

        # static folder (for style.css and favicon)
        if self.static_folder is None:
            self.static_folder = os.path.dirname(__file__)
        app.mount("/static", StaticFiles(directory=self.static_folder), name="static")

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
        # API interface - ../api/command or ../api JSON
        # ******************************************************************************

        @app.post("/api", response_class=JSONResponse)
        @app.get("/api/{command:path}", response_class=JSONResponse)
        async def api(request: Request, command: str = None):
            """
            Remote web api commands.
            """

            # JSON
            if command is None:
                args = await request.json()
                try:
                    command = getattr(azcam.db.api, args["command"])

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

            try:
                kwargs = qpars._dict

                caller = getattr(azcam.db.api, url)
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

            if self.logcommands:
                azcam.log(response, prefix="---->   ")

            return JSONResponse(response)

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
