from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import dash_daq as daq

import azcam


def detector_card():
    """
    Create detector card.
    """

    # First Column
    first_col_input = html.Div(
        [
            daq.NumericInput(id="first_col", label="First column", size=100, value=1),
        ]
    )

    @callback(
        Output("hidden_div", "children", allow_duplicate=True),
        Input("first_col", "value"),
        prevent_initial_call=True,
    )
    def first_col_callback(value):
        azcam.db.tools["exposure"].set_roi(first_col=int(value))
        return

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
        azcam.db.tools["exposure"].set_roi(last_col=int(value))
        return

    # Column binning
    col_bin_input = html.Div(
        [
            daq.NumericInput(id="col_bin", label="Column binning", size=100, value=1),
        ]
    )

    @callback(
        Output("hidden_div", "children", allow_duplicate=True),
        Input("col_bin", "value"),
        prevent_initial_call=True,
    )
    def col_bin_callback(value):
        azcam.db.tools["exposure"].set_roi(col_bin=int(value))
        return

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
        azcam.db.tools["exposure"].set_roi(first_row=int(value))
        return

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
        azcam.db.tools["exposure"].set_roi(last_row=int(value))
        return

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
        azcam.db.tools["exposure"].set_roi(row_bin=int(value))
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
        azcam.db.tools["exposure"].roi_reset()

        return

    @callback(
        Output("hidden_div", "children", allow_duplicate=True),
        Input("detpars_btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def on_button_click_detpars(n):
        azcam.db.tools["exposure"].set_roi()

        return

    detector_card = dbc.Card(
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

    return detector_card
