"""
Browser-based azcam tools.
"""

import os

import azcam
import azcam.server

from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates


class Status(object):
    """
    Implement a fastapi based web status page.
    """

    def __init__(self, webserver=None):

        self.webserver = webserver
        self.message = ""

        self.root_folder = os.path.dirname(__file__)
        self.static_files = {
            "style": [
                "/style_status.css",
                os.path.join(self.root_folder, "style_status.css"),
            ],
            "javascript": ["/status.js", os.path.join(self.root_folder, "status.js")],
        }

        self.router = APIRouter(
            prefix="/status",
        )

    def initialize(self):
        """
        Initialize status.
        """

        self.templates = Jinja2Templates(directory=self.root_folder)

        @self.router.get("/", response_class=HTMLResponse)
        def status(request: Request):
            templates = Jinja2Templates(directory=self.root_folder)
            return templates.TemplateResponse(
                "status.html",
                {"request": request, "message": self.message},
            )

        @self.router.get(self.static_files["style"][0], include_in_schema=False)
        async def style():
            return FileResponse(self.static_files["style"][1])

        @self.router.get(self.static_files["javascript"][0], include_in_schema=False)
        async def javascript():
            return FileResponse(self.static_files["javascript"][1])

        self.webserver.add_router(self.router)

        return
