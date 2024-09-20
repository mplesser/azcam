from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import dash_daq as daq

import azcam


def options_card():
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
        azcam.db.tools["exposure"].flush_array = int(value)
        return

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
        azcam.db.tools["exposure"].display_image = int(value)
        return

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
        try:
            azcam.db.tools["instrument"].is_enabled = int(value)
        except Exception:
            azcam.log("instrument not defined")
        return

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
        try:
            azcam.db.tools["telescope"].is_enabled = int(value)
        except Exception:
            azcam.log("telescope not defined")
        return

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
        azcam.db.tools["exposure"].auto_title = int(value)
        return

    options_card = dbc.Card(
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

    return options_card
