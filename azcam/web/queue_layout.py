from dash import html, dcc, callback, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import dash_daq as daq

import azcam
import azcam.web.queue_ops as qops


def queue_layout():
    """
    Create layout for queue control.
    """

    # buttons for queue control

    button_group = dbc.ButtonGroup(
        [
            dbc.Button("Run script", id="runscript_btn", className="m-1", n_clicks=0),
            dbc.Button(
                "Pause/Resume script", id="pausescript_btn", className="m-1", n_clicks=0
            ),
            dbc.Button(
                "Abort script", id="abortscript_btn", className="m-1", n_clicks=0
            ),
        ],
        vertical=False,
    )

    @callback(
        Output("hidden_divq", "children", allow_duplicate=True),
        Input("runscript_btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def on_button_click_run(n):
        try:
            qops.execute()
        except Exception as e:
            print(e)
        return

    @callback(
        Output("hidden_divq", "children", allow_duplicate=True),
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
        Output("hidden_divq", "children", allow_duplicate=True),
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

    # cycles to run script

    cycles_input = html.Div(
        [
            dbc.Label("Cycles", width=2),
            daq.NumericInput(id="cycles", value=1, size=100),
        ]
    )

    @callback(
        Output("hidden_divq", "children", allow_duplicate=True),
        Input("cycles", "value"),
        prevent_initial_call=True,
    )
    def cycles_callback(value):
        print(f"Cycle is {int(value)}")
        return

    # script loading

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

    @callback(
        Output("output-data-upload", "children"),
        Input("upload-data", "contents"),
        State("upload-data", "filename"),
        # State("upload-data", "last_modified"),
    )
    def update_output(list_of_contents, filename):

        if list_of_contents is not None:
            children = [qops.parse_script(list_of_contents, filename)]
            return children

    # interval update
    @callback(
        Output("message_queue", "children"),
        Input("queue_interval", "n_intervals"),
    )
    def update_queue(n=0):
        """
        Update queue status.
        """

        # the return order must match Output order

        return azcam.db.queueserver._queue_message

    # define page layout

    page_layout = dbc.Card(
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
                        [dbc.Col(cycles_input)],
                    ),
                    dbc.Row(
                        [
                            html.Div(id="message_queue"),
                        ]
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

    return page_layout
