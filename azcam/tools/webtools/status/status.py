"""
Browser-based azcam tools.
"""

import os

import azcam

from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


class Status(object):
    """
    Implement a fastapi based web status page.
    """

    def __init__(self):

        self.message = ""

        self.root_folder = os.path.dirname(__file__)

        self.router = APIRouter(
            prefix="/status",
        )

        azcam.db.tools["webserver"].app.mount(
            "/status/code",
            StaticFiles(directory=os.path.join(self.root_folder, "code")),
            name="code",
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

        azcam.db.tools["webserver"].add_router(self.router)

        return
