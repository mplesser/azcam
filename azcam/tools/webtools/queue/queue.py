"""
Browser-based queue observing.
"""

import os

import azcam

from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates


class Queue(object):
    """
    Implement a fastapi based queue observing API.
    """

    def __init__(self):

        self.message = ""

        self.root_folder = os.path.dirname(__file__)

        self.static_files = {
            "style": ["/style_queue.css", os.path.join(self.root_folder, "style_queue.css")],
            "javascript": ["/queue.js", os.path.join(self.root_folder, "queue.js")],
        }

        self.router = APIRouter(
            prefix="/queue",
        )

    def initialize(self):
        """
        Initialize queue.
        """

        self.templates = Jinja2Templates(directory=self.root_folder)

        @self.router.get("/", response_class=HTMLResponse)
        def status(request: Request):
            templates = Jinja2Templates(directory=self.root_folder)
            return templates.TemplateResponse(
                "queue.html",
                {"request": request, "message": self.message},
            )

        @self.router.get(self.static_files["style"][0], include_in_schema=False)
        async def style():
            return FileResponse(self.static_files["style"][1])

        @self.router.get(self.static_files["javascript"][0], include_in_schema=False)
        async def javascript():
            return FileResponse(self.static_files["javascript"][1])

        azcam.db.tools["webserver"].add_router(self.router)

        return
