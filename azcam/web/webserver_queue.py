"""
DASH web server for azcam
"""

import threading
import logging

from dash import Dash, html, dcc, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import dash_daq as daq

import azcam
from azcam.web.queue_card import queue_card


class QueueServer(object):
    """
    Web server for queue operations using Dash (plotly).
    """

    def __init__(self) -> None:

        self.port = 2406
        self.logcommands = 0
        self.logstatus = 0
        azcam.db.queueserver = self
        azcam.db._command = {}  # command dict

        self.app = Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=False,
        )
        logging.getLogger("werkzeug").setLevel(logging.CRITICAL)  # stop messages

        self.queue_card = queue_card()

        # app layout
        self.app.layout = html.Div(
            [
                self.queue_card,
                html.Div(id="hidden_div", hidden=True),
                dcc.Interval("queue_interval", interval=500, n_intervals=0),
            ]
        )

    # interval update
    @callback(
        Output("message_queue", "children"),
        Input("queue_interval", "n_intervals"),
    )
    def update_queue(n):
        """
        Update queue status.
        """

        # the return order must match Output order
        data = "mike"

        return [
            str(n),
        ]

        return

    def set_message(self, message: str = "") -> None:
        """
        Set the browser message.
        """

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
