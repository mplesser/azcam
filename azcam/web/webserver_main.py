"""
DASH web server for azcam
"""

import threading
import logging

from dash import Dash, html, dcc, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import dash_daq as daq

import azcam
from azcam.web.exposure_card import exposure_card
from azcam.web.status_card import status_card
from azcam.web.filename_card import filename_card
from azcam.web.detector_card import detector_card
from azcam.web.options_card import options_card
from azcam.web.tabs import tabs_buttons, tabs


class WebServer(object):
    """
    Web server using Dash (plotly).
    """

    def __init__(self) -> None:

        self.port = 2403
        self.logcommands = 0
        self.logstatus = 0
        azcam.db.webserver = self
        azcam.db._command = {}  # command dict

        self.app = Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=False,
        )
        logging.getLogger("werkzeug").setLevel(logging.CRITICAL)  # stop messages

        self.exposure_card = exposure_card()
        self.status_card = status_card()
        self.filename_card = filename_card()
        self.detector_card = detector_card()
        self.options_card = options_card()

        self.tabs_buttons = tabs_buttons()
        self.tabs = tabs(self)

        # app layout
        self.app.layout = html.Div(
            [
                self.tabs_buttons,
                self.tabs,
                html.Div(id="hidden_div", hidden=True),
                dcc.Interval("status_interval", interval=1_000, n_intervals=0),
            ]
        )

        return

    def set_message(self, message: str = "") -> None:
        """
        Set the browser message.
        """

        azcam.db.tools["exposure"].message = repr(message)
        return

    def start(self):
        kwargs = {
            "debug": False,
            "port": azcam.db.cmdserver.port + 1,
            "host": "localhost",
            "use_reloader": False,
        }

        azcam.log(f"Starting web server on port {kwargs['port']}")
        if 1:
            thread = threading.Thread(
                target=self.app.run,
                name="azcam_webserver",
                kwargs=kwargs,
            )
            thread.daemon = True  # terminates when main process exits
            thread.start()
        else:
            self.app.run(**kwargs)
