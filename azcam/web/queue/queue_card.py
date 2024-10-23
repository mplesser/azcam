import base64
import datetime
import io

from dash import html, dcc, callback, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import dash_daq as daq
import pandas as pd

import azcam
import azcam.web.queue.queue_ops as qops


def create_button_group():
    """
    Create button group for queue control.
    """

    button_group = dbc.ButtonGroup(
        [
            dbc.Button("Run script", id="run_btn", className="m-1", n_clicks=0),
            dbc.Button("Pause/Resume", id="pause_btn", className="m-1", n_clicks=0),
            dbc.Button("Abort script", id="abort_btn", className="m-1", n_clicks=0),
        ],
        vertical=False,
    )

    @callback(
        Output("hidden_div1", "children", allow_duplicate=True),
        Input("run_btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def on_button_click_run(n):
        try:
            qops.execute()
        except Exception as e:
            print(e)
        return

    @callback(
        Output("hidden_div1", "children", allow_duplicate=True),
        Input("pausescript_btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def on_button_click_pausescript(n):
        try:
            # azcam.db.tools["exposure"].reset()
            pass
        except Exception as e:
            print(e)
        return

    @callback(
        Output("hidden_div1", "children", allow_duplicate=True),
        Input("abortscript_btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def on_button_click_abortscript(n):
        try:
            pass
            # azcam.db.tools["exposure"].abort()
        except Exception as e:
            print(e)
        return

    return button_group


def queue_card():
    """
    Create card for queue control.
    """

    cycles_input = html.Div(
        [
            dbc.Label("Cycles"),
            daq.NumericInput(id="cycles", value=1, size=100),
        ]
    )

    @callback(
        Output("hidden_div1", "children", allow_duplicate=True),
        Input("cycles", "value"),
        prevent_initial_call=True,
    )
    def cycles_callback(value):
        return

    altaz_input = html.Div(
        [
            dbc.Label("Use Alt/Az"),
            dbc.Checkbox(id="altaz", value=True),
        ]
    )

    @callback(
        Output("hidden_div1", "children", allow_duplicate=True),
        Input("altaz", "value"),
        prevent_initial_call=True,
    )
    def altaz_callback(value):
        return

    script_input = html.Div(
        [
            dcc.Upload(
                id="upload-data",
                children=html.Div(["Drag and Drop or ", html.A("Select Script")]),
                style={
                    "width": "100%",
                    "height": "60px",
                    "lineHeight": "60px",
                    "borderWidth": "1px",
                    "borderStyle": "dashed",
                    "borderRadius": "5px",
                    "textAlign": "center",
                    "margin": "10px",
                },
                multiple=False,
            ),
        ]
    )

    def parse_script(contents, filename):
        content_type, content_string = contents.split(",")

        decoded = base64.b64decode(content_string)
        try:
            if "csv" in filename:
                # Assume that the user uploaded a CSV file
                df = pd.read_csv(
                    io.StringIO(decoded.decode("utf-8")),
                    dtype=str,
                    keep_default_na=False,
                    skipinitialspace=True,
                )
                azcam.db.queue_df = df
        except Exception as e:
            print(e)
            return html.Div(["There was an error processing this file."])

        return html.Div(
            [
                html.H5(filename),
                dash_table.DataTable(
                    df.to_dict("records"), [{"name": i, "id": i} for i in df.columns]
                ),
            ]
        )

    @callback(
        Output("output-data-upload", "children"),
        Input("upload-data", "contents"),
        State("upload-data", "filename"),
        # State("upload-data", "last_modified"),
    )
    def update_output(list_of_contents, filename):

        if list_of_contents is not None:
            children = [parse_script(list_of_contents, filename)]
            return children

    button_group = create_button_group()

    queue_card = dbc.Card(
        [
            dbc.CardHeader("Observing Queue Control", style={"font-weight": "bold"}),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            button_group,
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(script_input),
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(cycles_input),
                            dbc.Col(altaz_input),
                        ],
                    ),
                    dbc.Row(
                        [
                            html.Div(id="hidden_div1"),
                        ],
                    ),
                    dbc.Row(
                        [
                            html.Div(id="message_queue"),
                        ],
                    ),
                ]
            ),
            dbc.CardFooter(
                [
                    html.Div(id="output-data-upload"),
                ]
            ),
        ]
    )

    return queue_card
