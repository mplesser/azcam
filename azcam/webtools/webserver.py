"""
Configure and start fastapi application using uvicorn.
Import this after all configuration has been completed.
All API commands suported here must start with ""http://locahost:xxxx/api/" where xxxx is the
port number like 2402.

Query string example: "http://localhost:2402/api/instrument/set_filter?filter=1&filter_id=2"

JSON example:
    data = {
        "tool": "parameters",
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
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import azcam
import azcam.exceptions


class WebServer(object):
    """
    Azcam web server.
    """

    def __init__(self):
        self.templates_folder = ""
        self.index = "index.html"
        self.upload_folder = None
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

        if self.upload_folder is None:
            self.upload_folder = os.path.join(self.datafolder, "uploads")

        if self.favicon_path is None:
            self.favicon_path = os.path.join(os.path.dirname(__file__), "favicon.ico")

        # static folder - /static
        # app.mount(
        #     "/static",
        #     StaticFiles(directory=os.path.join(self.datafolder, "static")),
        #     name="static",
        # )

        # templates folder
        try:
            templates = Jinja2Templates(directory=os.path.dirname(self.index))
        except Exception:
            pass
        # log_templates = Jinja2Templates(directory=os.path.dirname(azcam.logger.logfile))

        # log folder - /log
        # app.mount(
        #     "/logs",
        #     StaticFiles(directory=os.path.dirname(azcam.logger.logfile), html=False),
        #     name="logs",
        # )

        # ******************************************************************************
        # Home - /
        # ******************************************************************************
        @app.get("/", response_class=HTMLResponse)
        def home(request: Request):
            index = os.path.basename(self.index)
            return templates.TemplateResponse(
                index, {"request": request, "message": self.message}
            )

        # ******************************************************************************
        # API interface - ../api/tool/command or ../api JSON
        # ******************************************************************************
        @app.post("/api", response_class=JSONResponse)
        @app.get("/api/{command:path}", response_class=JSONResponse)
        async def api(request: Request, command: str = None):
            """
            Remote web api commands.
            """

            # print("command:", command)
            # print("qpars:", request.query_params)

            # JSON request
            if command is None:
                args = await request.json()

                try:
                    toolid = azcam.db.tools[args["tool"]]
                    command = getattr(toolid, args["command"])
                    arglist = args["args"]
                    kwargs = args["kwargs"]

                    response = api.command(toolid, command, arglist, kwars)

                    reply = command(*arglist, **kwargs)
                except Exception as e:
                    reply = repr(e)
                    azcam.log(e)

                response = {
                    "message": "Finished",
                    "command": f"{args['tool']}.{args['command']}",
                    "data": reply,
                }

                return JSONResponse(response)

            # query string request
            url = command
            qpars = request.query_params

            if self.logcommands:
                if self.logstatus:
                    azcam.log(url, qpars, prefix="Web-> ")
                else:
                    if not ("get_status" in url or "watchdog" in url):
                        azcam.log(url, qpars, prefix="Web-> ")

            reply = self.web_command(url, qpars)

            if self.logcommands:
                if self.logstatus:
                    azcam.log(reply, prefix="Web->   ")
                else:
                    if not ("get_status" in url or "watchdog" in url):
                        azcam.log(reply["data"], prefix="Web->   ")

            return JSONResponse(reply)

        @app.get("/favicon.ico", include_in_schema=False)
        async def favicon():
            return FileResponse(self.favicon_path)

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
        kwargs = {"port": self.port, "host": "localhost", "log_level": "critical"}

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
            obj, method, kwargs = self.parse(url, qpars)

            # objects = obj.split(".")

            objid = azcam.db.tools["api"]

            # # special case temporarily for parameters
            # if objects[0] == "parameters":
            #     if len(objects) == 1:
            #         objid = azcam.db.parameters
            #     elif len(objects) == 2:
            #         objid = getattr(azcam.db.parameters, objects[1])
            #     elif len(objects) == 3:
            #         objid = getattr(
            #             getattr(azcam.db.parameters, objects[1]), objects[2]
            #         )
            #     elif len(objects) == 4:
            #         objid = getattr(
            #             getattr(getattr(azcam.db.parameters, objects[1]), objects[2]),
            #             objects[3],
            #         )
            #     else:
            #         objid = None  # too complicated for now

            # elif objects[0] in azcam.db.tools:
            #     if len(objects) == 1:
            #         objid = azcam.db.tools[obj]
            #     elif len(objects) == 2:
            #         objid = getattr(azcam.db.tools.get(objects[0]), objects[1])
            #     elif len(objects) == 3:
            #         objid = getattr(
            #             getattr(azcam.db.tools.get(objects[0]), objects[1]), objects[2]
            #         )
            #     else:
            #         objid = None  # too complicated for now

            # else:
            #     raise azcam.exceptions.AzcamError(
            #         f"remote call not allowed in API: {obj}", 4
            #     )

            caller = getattr(objid, method)
            reply = caller() if kwargs is None else caller(**kwargs)

        except azcam.exceptions.AzcamError as e:
            azcam.log(f"web_command error: {e}")
            if e.error_code == 4:
                reply = "remote call not allowed"
            else:
                reply = f"web_command error: {repr(e)}"
        except Exception as e:
            azcam.log(e)
            reply = f"API command error: {url}"

        # generic response
        response = {
            "message": "Finished",
            "command": url,
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
        tokens = url
        method = tokens

        # get arguments
        kwargs = qpars._dict

        return None, method, kwargs
