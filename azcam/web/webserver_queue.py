"""
DASH web server for azcam
"""

import threading
import logging

from dash import Dash, html, dcc, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import dash_daq as daq

import azcam
from azcam.web.queue_layout import queue_layout


class QueueServer(object):
    """
    Web server for queue operations using Dash (plotly).
    """

    def __init__(self) -> None:

        self.port = 2406
        self.logcommands = 0
        self.logstatus = 0
        self._queue_message = ""

        azcam.db.queueserver = self

        self.app = Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=False,
            title="AzCam Queue",
            update_title="",
        )
        logging.getLogger("werkzeug").setLevel(logging.CRITICAL)  # stop messages

        # app layout
        self.app.layout = html.Div(
            [
                queue_layout(),
                html.Div(id="hidden_divq"),
                dcc.Interval("queue_interval", interval=1000, n_intervals=0),
            ]
        )

    def set_message(self, message: str = "") -> None:
        """
        Set the browser message.
        """

        azcam.db.queueserver._queue_message = message

        return

    def start(self):
        kwargs = {
            "debug": False,
            "port": azcam.db.cmdserver.port + 4,
            "host": "localhost",
            "use_reloader": False,
        }

        azcam.log(f"Starting queue server on port {kwargs['port']}")
        if 1:
            thread = threading.Thread(
                target=self.app.run,
                name="azcam_queueserver",
                kwargs=kwargs,
            )
            thread.daemon = True  # terminates when main process exits
            thread.start()
        else:
            self.app.run(**kwargs)
