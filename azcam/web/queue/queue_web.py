"""
DASH web server for azcam
"""

import threading
import logging

from dash import Dash, html, dcc, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import dash_daq as daq

import azcam
from azcam.web.queue.queue_card import queue_card


class QueueWeb(object):
    """
    Web code for queue operations using Dash (plotly).
    """

    def __init__(self) -> None:

        azcam.db.queueserver = self

        self.app = Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=False,
            requests_pathname_prefix="/queue/",
        )
        logging.getLogger("werkzeug").setLevel(logging.CRITICAL)  # stop messages

        self.queue_card = queue_card()

        # app layout
        self.app.layout = html.Div(
            [
                self.queue_card,
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
