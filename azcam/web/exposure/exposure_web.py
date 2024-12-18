"""
DASH web server for azcam
"""

import threading
import logging

from dash import Dash, html, dcc, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import dash_daq as daq

import azcam
from azcam.web.exposure.exposure_card import exposure_card
from azcam.web.exposure.status_card import status_card
from azcam.web.exposure.filename_card import filename_card
from azcam.web.exposure.detector_card import detector_card
from azcam.web.exposure.options_card import options_card
from azcam.web.exposure.tabs import tabs_buttons, tabs


class ExposureWeb(object):
    """
    Web server using Dash (plotly).
    """

    def __init__(self) -> None:

        azcam.db.expserver = self

        self.app = Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=False,
            requests_pathname_prefix="/exposure/",
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
                dcc.Interval("expstatus_interval", interval=1_000, n_intervals=0),
            ]
        )

        return

    def set_message(self, message: str = "") -> None:
        """
        Set the browser message.
        """

        azcam.db.tools["exposure"].message = repr(message)
        return
