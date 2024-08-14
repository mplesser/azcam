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
from azcam.web.tabs import tabs_buttons, tabs


class WebServer(object):
    """
    Test web server using Dash.
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

        self.create_filename_card()
        self.create_detector_card()
        self.create_options_card()

        self.tabs_buttons = tabs_buttons()
        self.tabs = tabs(self)
        self.create_layout()

        return

    def create_filename_card(self):
        """
        Create filename card.
        """

        """
        Directory with browse
        Rootname
        Seq Num spinner
        Image Format NO
        
        Auto inc
        Overwrite
        Inc. seq
        Autoname
        test image
        """

        curfolder = "/data"

        folderselect = html.Div(
            [
                dbc.Label("Image folder"),
                dbc.Input(
                    id="folderselect",
                    placeholder="Enter image file folder...",
                    type="text",
                    style={"display": "inline-block"},
                ),
            ]
        )

        rootselect = html.Div(
            [
                dbc.Label("Image root name"),
                dbc.Input(
                    id="rootselect",
                    placeholder="Enter image root name...",
                    type="text",
                    style={"display": "inline-block"},
                ),
            ]
        )

        seqnumselect = html.Div(
            [
                dbc.Label("Image sequence number"),
                dbc.Input(
                    id="seqnumselect",
                    placeholder="Enter image sequence number...",
                    type="number",
                    min=0,
                    style={"display": "inline-block"},
                ),
            ]
        )

        filenamechecks_input = dcc.Checklist(
            [
                {
                    "label": "Auto increment",
                    "value": "autoinc",
                    "title": "check to auto increment image sequence number",
                },
                {
                    "label": "Overwrite existing image",
                    "value": "overwrite",
                },
                {
                    "label": "Include sequence number",
                    "value": "includeseqnum",
                },
                {
                    "label": "Auto name",
                    "value": "autoname",
                    "title": "check to inlcude Object Type in image filename",
                },
            ],
            id="filename_checks",
            value=["overwrite"],
            inline=False,
        )
        checks_filename = html.Div(filenamechecks_input)

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("filename_checks", "value"),
            prevent_initial_call=True,
        )
        def image_test_callback(value):
            azcam.db.tools["exposure"].message = repr(value)
            return value

        # apply button - all options on this page
        apply_filename_btn = dbc.Button(
            "Apply All",
            id="apply_filename_btn",
            style={"margin-top": "1em"},
            n_clicks=0,
        )

        @callback(
            Output("fileselect_out", "children", allow_duplicate=True),
            Input("apply_filename_btn", "n_clicks"),
            State("seqnumselect", "value"),
            State("rootselect", "value"),
            State("folderselect", "value"),
            prevent_initial_call=True,
        )
        def on_button_click_apply_filename(n, seqnum, root, folder):
            print(seqnum, root, folder)
            try:
                pass
                # azcam.db.tools["exposure"].expose()
            except Exception as e:
                print(e)
            return

        self.filename_card = dbc.Card(
            [
                dbc.CardHeader("Filename Parameters", style={"font-weight": "bold"}),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        folderselect,
                                        rootselect,
                                        seqnumselect,
                                    ]
                                ),
                                dbc.Col(
                                    [
                                        checks_filename,
                                    ]
                                ),
                            ]
                        ),
                        dbc.Row(
                            [
                                apply_filename_btn,
                                html.Div(id="fileselect_out"),
                            ]
                        ),
                    ]
                ),
            ]
        )

        return

    def create_detector_card(self):
        """
        Create detector card.
        """

        # First Column
        first_col_input = html.Div(
            [
                daq.NumericInput(
                    id="first_col", label="First column", size=100, value=1
                ),
            ]
        )

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("first_col", "value"),
            prevent_initial_call=True,
        )
        def first_col_callback(value):
            azcam.db._command["first_col"] = 1 if value is None else value
            azcam.db.tools["exposure"].message = repr(azcam.db._command)
            return value

        # Last Column
        last_col_input = html.Div(
            [
                daq.NumericInput(id="last_col", label="Last column", size=100, value=1),
            ]
        )

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("last_col", "value"),
            prevent_initial_call=True,
        )
        def last_col_callback(value):
            azcam.db._command["last_col"] = 1 if value is None else value
            azcam.db.tools["exposure"].message = repr(azcam.db._command)
            return value

        # Column binning
        col_bin_input = html.Div(
            [
                daq.NumericInput(
                    id="col_bin", label="Column binning", size=100, value=1
                ),
            ]
        )

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("col_bin", "value"),
            prevent_initial_call=True,
        )
        def col_bin_callback(value):
            azcam.db._command["col_bin"] = 1 if value is None else value
            azcam.db.tools["exposure"].message = repr(azcam.db._command)
            return value

        # First Row
        first_row_input = html.Div(
            [
                daq.NumericInput(id="first_row", label="First row", size=100, value=1),
            ]
        )

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("first_row", "value"),
            prevent_initial_call=True,
        )
        def first_row_callback(value):
            azcam.db._command["first_row"] = 1 if value is None else value
            azcam.db.tools["exposure"].message = repr(azcam.db._command)
            return value

        # Last Row
        last_row_input = html.Div(
            [
                daq.NumericInput(id="last_row", label="Last row", size=100, value=1),
            ]
        )

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("last_row", "value"),
            prevent_initial_call=True,
        )
        def last_row_callback(value):
            azcam.db._command["last_row"] = 1 if value is None else value
            azcam.db.tools["exposure"].message = repr(azcam.db._command)
            return value

        # Row binning
        row_bin_input = html.Div(
            [
                daq.NumericInput(id="row_bin", label="Row binning", size=100, value=1),
            ]
        )

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("row_bin", "value"),
            prevent_initial_call=True,
        )
        def row_bin_callback(value):
            azcam.db._command["row_bin"] = 1 if value is None else value
            azcam.db.tools["exposure"].message = repr(azcam.db._command)
            return value

        detector_button_group = dbc.ButtonGroup(
            [
                dbc.Button(
                    "Set Full Frame", id="fullframe_btn", className="m-1", n_clicks=0
                ),
                dbc.Button("Apply All", id="detpars_btn", className="m-1", n_clicks=0),
            ],
            vertical=False,
        )

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("fullframe_btn", "n_clicks"),
            prevent_initial_call=True,
        )
        def on_button_click_fullframe(n):
            try:
                pass
                # azcam.db.tools["exposure"].expose()
            except Exception as e:
                print(e)
            return

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("detpars_btn", "n_clicks"),
            prevent_initial_call=True,
        )
        def on_button_click_detpars(n):
            try:
                pass
                # azcam.db.tools["exposure"].sequence()
            except Exception as e:
                print(e)
            return

        self.detector_card = dbc.Card(
            [
                dbc.CardHeader("Detector Parameters", style={"font-weight": "bold"}),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(first_col_input, width=2),
                                dbc.Col(last_col_input, width=2),
                                dbc.Col(col_bin_input, width=2),
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(first_row_input, width=2),
                                dbc.Col(last_row_input, width=2),
                                dbc.Col(row_bin_input, width=2),
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(detector_button_group),
                            ]
                        ),
                    ]
                ),
            ]
        )

        # self.detector_card = dbc.Card(dbc.CardBody([html.Div("Detector not yet")]))

        return

    def create_options_card(self):
        """
        Create options card.
        """

        # flush sensor
        flush_input = html.Div(
            [
                dbc.Checkbox(
                    id="flush_sensor",
                    label="Clear sensor before each exposure",
                    value=True,
                ),
            ]
        )

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("flush_sensor", "value"),
            prevent_initial_call=True,
        )
        def flush_sensor_callback(value):
            return value

        # display image
        display_image_input = html.Div(
            [
                dbc.Checkbox(
                    id="display_image",
                    label="Display image from server",
                    value=True,
                ),
            ]
        )

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("display_image", "value"),
            prevent_initial_call=True,
        )
        def display_image_callback(value):
            return value

        # enable instrument
        enable_instrument_input = html.Div(
            [
                dbc.Checkbox(
                    id="enable_instrument",
                    label="Enable instrument",
                    value=True,
                ),
            ]
        )

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("enable_instrument", "value"),
            prevent_initial_call=True,
        )
        def enable_instrument_callback(value):
            return value

        # enable telescope
        enable_telescope_input = html.Div(
            [
                dbc.Checkbox(
                    id="enable_telescope",
                    label="Enable telescope",
                    value=True,
                ),
            ]
        )

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("enable_telescope", "value"),
            prevent_initial_call=True,
        )
        def enable_telescope_callback(value):
            return value

        # auto title images
        auto_title_input = html.Div(
            [
                dbc.Checkbox(
                    id="auto_title",
                    label="Auto title images",
                    value=True,
                ),
            ]
        )

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("auto_title", "value"),
            prevent_initial_call=True,
        )
        def auto_title_callback(value):
            return value

        self.options_card = dbc.Card(
            [
                dbc.CardHeader("Options", style={"font-weight": "bold"}),
                dbc.CardBody(
                    [
                        flush_input,
                        display_image_input,
                        enable_instrument_input,
                        enable_telescope_input,
                        auto_title_input,
                    ]
                ),
            ]
        )

        return

    def create_layout(self):
        """
        Create layout for web server.
        """

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

    def start(self):
        kwargs = {
            "debug": False,
            "port": azcam.db.cmdserver.port + 1,
            "host": "localhost",
            "use_reloader": False,
        }

        if 1:
            thread = threading.Thread(
                target=self.app.run,
                name="azcam_webserver",
                kwargs=kwargs,
            )
            thread.daemon = True  # terminates when main process exits
            thread.start()
        else:
            self.app.run(port="2403", debug=True)


if __name__ == "__main__":
    webserver = WebServerDash()
    webserver.app.run(debug=False, port=2403)
    # webserver.start()
    input("waiting for web server here...")
