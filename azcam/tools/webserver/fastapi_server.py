"""
Configure and start fastapi application using uvicorn.
Import this after all configuration has been completed.
All API commands suported here must start with ""http://locahost:2402/api/".

URL example: "http://localhost:2402/api/instrument/set_filter?filter=1&filter_id=2"

Default response is JSON:
    response = {
        "message": "Finished",
        "command": urlparse(url).path,
        "data": reply,
    }
If webserver.return_json is False, then just "data" is returned.

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
        self.return_json = 0

        # port for webserver
        self.port = None

        self.is_running = 0

        azcam.db.tools["webserver"] = self

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
        # log_templates = Jinja2Templates(directory=os.path.dirname(azcam.db.logger.logfile))

        # log folder - /log
        # app.mount(
        #     "/logs",
        #     StaticFiles(directory=os.path.dirname(azcam.db.logger.logfile), html=False),
        #     name="logs",
        # )

        # ******************************************************************************
        # Home - /
        # ******************************************************************************
        @app.get("/", response_class=HTMLResponse)
        def home(request: Request):
            index = os.path.basename(self.index)
            return templates.TemplateResponse(index, {"request": request, "message": self.message})

        # ******************************************************************************
        # API command - /api/tool/command
        # ******************************************************************************
        @app.get("/api/{command:path}", response_class=JSONResponse)
        def api(request: Request, command: str):
            """
            Remote web api commands. such as: /api/expose or /api/exposure/reset
            """

            url = command
            qpars = request.query_params

            if self.logcommands:
                if self.logstatus:
                    azcam.log(url, prefix="Web-> ")
                else:
                    if not ("/get_status" in url or "/watchdog" in url):
                        azcam.log(url, prefix="Web-> ")

            reply = self.web_command(url, qpars)

            if self.logcommands:
                if self.logstatus:
                    azcam.log(reply, prefix="Web->   ")
                else:
                    if not ("/get_status" in url or "/watchdog" in url):
                        azcam.log(reply, prefix="Web->   ")

            return JSONResponse(reply)

        # ******************************************************************************
        # JSON API command - .../japi/tool/command
        # ******************************************************************************
        @app.post("/japi", response_class=JSONResponse)
        async def japi(request: Request):
            """
            Remote web api commands using JSON.
            """

            args = await request.json()

            try:
                toolid = azcam.db.tools[args["tool"]]
                command = getattr(toolid, args["command"])

                arglist = args["args"]
                kwargs = args["kwargs"]
                reply = command(*arglist, **kwargs)
            except Exception as e:
                azcam.log(e)

            response = {
                "message": "Finished",
                "command": f"{args['tool']}.{args['command']}",
                "data": reply,
            }

            return JSONResponse(response)

        @app.get('/favicon.ico', include_in_schema=False)
        async def favicon():
            return FileResponse(self.favicon_path)

    def add_router(self, router):
        """
        Add router.
        """

        self.app.include_router(router)

        return

    def test_router(self):

        fake_items_db = {"plumbus": {"name": "Plumbus"}, "gun": {"name": "Portal Gun"}}

        router = APIRouter(
            prefix="/items",
            tags=["items"],
            responses={404: {"description": "Item not found"}},
        )

        @router.get("/")
        async def read_items():
            return fake_items_db

        @router.get("/{item_id}")
        async def read_item(item_id: str):
            if item_id not in fake_items_db:
                raise HTTPException(status_code=404, detail="Item not found")
            return {"name": fake_items_db[item_id]["name"], "item_id": item_id}

        self.add_router(router)

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

        thread = threading.Thread(target=uvicorn.run, name="uvicorn", args=arglist, kwargs=kwargs)
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

            # primary object must be in db.tools
            objects = obj.split(".")
            if objects[0] not in azcam.db.tools:
                raise azcam.AzcamError(f"remote call not allowed in API: {obj}", 4)

            if len(objects) == 1:
                objid = azcam.db.tools[obj]
            elif len(objects) == 2:
                objid = getattr(azcam.db.tools.get(objects[0]), objects[1])
            elif len(objects) == 3:
                objid = getattr(getattr(azcam.db.tools.get(objects[0]), objects[1]), objects[2])
            else:
                objid = None  # too complicated for now

            caller = getattr(objid, method)
            reply = caller() if kwargs is None else caller(**kwargs)

        except azcam.AzcamError as e:
            azcam.log(f"web_command error: {e}")
            if e.error_code == 4:
                reply = "remote call not allowed"
            else:
                reply = f"web_command error: {repr(e)}"
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
            raise e("Invalid API command - parse split")

        # get oject and method
        if len(tokens) != 2:
            raise azcam.AzcamError("Invalid API command - parse length")
        obj, method = tokens

        # get arguments
        kwargs = qpars._dict

        return obj, method, kwargs
