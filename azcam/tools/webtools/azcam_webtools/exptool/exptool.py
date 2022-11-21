"""
Browser-based exposure control.
"""

import os

import azcam

from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


class Exptool(object):
    """
    Implement a fastapi based web exposure control page.
    """

    def __init__(self):

        self.message = ""

        self.root_folder = os.path.dirname(__file__)

        self.router = APIRouter(
            prefix="/exptool",
        )

        azcam.db.tools["webserver"].app.mount(
            "/exptool/code",
            StaticFiles(directory=os.path.join(self.root_folder, "code")),
            name="code",
        )

    def initialize(self):
        """
        Initialize exptool.
        """

        self.templates = Jinja2Templates(directory=self.root_folder)

        @self.router.get("/", response_class=HTMLResponse)
        def status(request: Request):
            templates = Jinja2Templates(directory=self.root_folder)
            return templates.TemplateResponse(
                "exptool.html",
                {"request": request, "message": self.message},
            )

        azcam.db.tools["webserver"].add_router(self.router)

        return
