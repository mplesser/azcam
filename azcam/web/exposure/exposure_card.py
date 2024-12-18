from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import dash_daq as daq

import azcam


def create_button_group():
    """
    Create button group for exposure control.
    """

    button_group = dbc.ButtonGroup(
        [
            dbc.Button("Expose", id="expose_btn", className="m-1", n_clicks=0),
            dbc.Button("Sequence", id="sequence_btn", className="m-1", n_clicks=0),
            dbc.Button("Reset", id="reset_btn", className="m-1", n_clicks=0),
            dbc.Button("Abort", id="abort_btn", className="m-1", n_clicks=0),
            dbc.Button("Save Pars", id="savepars_btn", className="m-1", n_clicks=0),
        ],
        vertical=True,
    )

    @callback(
        Output("hidden_div", "children", allow_duplicate=True),
        Input("expose_btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def on_button_click_expose(n):
        try:
            azcam.db.tools["exposure"].expose()
        except Exception as e:
            print(e)
        return

    @callback(
        Output("hidden_div", "children", allow_duplicate=True),
        Input("sequence_btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def on_button_click_sequence(n):
        try:
            azcam.db.tools["exposure"].sequence()
        except Exception as e:
            print(e)
        return

    @callback(
        Output("hidden_div", "children", allow_duplicate=True),
        Input("reset_btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def on_button_click_reset(n):
        try:
            azcam.db.tools["exposure"].reset()
        except Exception as e:
            print(e)
        return

    @callback(
        Output("hidden_div", "children", allow_duplicate=True),
        Input("abort_btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def on_button_click_abort(n):
        try:
            azcam.db.tools["exposure"].abort()
        except Exception as e:
            print(e)
        return

    @callback(
        Output("hidden_div", "children", allow_duplicate=True),
        Input("savepars_btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def on_button_click_savepars(n):
        try:
            azcam.db.parameters.save_pars()
        except Exception as e:
            print(e)
        return

    return button_group


def exposure_card():
    """
    Create exposure card for exposure control.
    """

    options = [
        {"label": x, "value": x.lower()} for x in azcam.db.tools["exposure"].image_types
    ]

    image_type_dropdown = html.Div(
        [
            dbc.Label("Image Type"),
            dcc.Dropdown(
                options,
                id="image_type_dropdown",
                value="zero",
            ),
        ]
    )

    @callback(
        Output("hidden_div", "children", allow_duplicate=True),
        Input("image_type_dropdown", "value"),
        prevent_initial_call=True,
    )
    def image_type_callback(value):
        azcam.db.tools["exposure"].set_image_type(value)
        return ""

    exposure_time_input = html.Div(
        [
            dbc.Label("Exp. time [sec]"),
            daq.NumericInput(id="et", value=0.0, size=100),
        ]
    )

    @callback(
        Output("hidden_div", "children", allow_duplicate=True),
        Input("et", "value"),
        prevent_initial_call=True,
    )
    def exposure_time_callback(value):
        try:
            azcam.db.tools["exposure"].set_exposuretime(value)
        except Exception:
            pass  # controller may not be reset
        return ""

    image_title_input = html.Div(
        [
            dbc.Label("Image Title"),
            dbc.Input(
                id="title_input",
                placeholder="Enter image title...",
                type="text",
                style={"display": "inline-block"},
            ),
        ]
    )

    @callback(
        Output("hidden_div", "children", allow_duplicate=True),
        Input("title_input", "value"),
        prevent_initial_call=True,
    )
    def image_title_callback(value):
        azcam.db.tools["exposure"].set_image_title(value)
        return value

    test_image_input = html.Div(
        [
            dbc.Label("Test Image"),
            dbc.Checkbox(id="test_image", value=True),
        ]
    )

    @callback(
        Output("hidden_div", "children", allow_duplicate=True),
        Input("test_image", "value"),
        prevent_initial_call=True,
    )
    def image_test_callback(value):
        azcam.db.tools["exposure"].set_test_image(value)
        return value

    ###########################################################################
    # sequence pars
    ###########################################################################
    num_seq_images_input = html.Div(
        [
            daq.NumericInput(id="seq_num", label="Number seq. images", size=100),
        ]
    )

    @callback(
        Output("hidden_div", "children", allow_duplicate=True),
        Input("seq_num", "value"),
        prevent_initial_call=True,
    )
    def seq_total_callback(value):
        azcam.db.tools["exposure"].exposure_sequence_total = int(value)
        return value

    sequence_delay_input = html.Div(
        [
            daq.NumericInput(
                id="seq_delay",
                label="Seq. delay [sec]",
                size=100,
                style={"margin-top": "2"},
            ),
        ]
    )

    @callback(
        Output("hidden_div", "children", allow_duplicate=True),
        Input("seq_delay", "value"),
        prevent_initial_call=True,
    )
    def seq_delay_callback(value):
        azcam.db.tools["exposure"].exposure_sequence_delay = float(value)
        return value

    button_group = create_button_group()

    exposure_card = dbc.Card(
        [
            dbc.CardHeader("Exposure Control", style={"font-weight": "bold"}),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(button_group, width=2),
                            dbc.Col(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(image_type_dropdown),
                                            dbc.Col(test_image_input),
                                            dbc.Col(exposure_time_input),
                                        ]
                                    ),
                                    dbc.Row(
                                        [image_title_input],
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(num_seq_images_input, width=3),
                                            dbc.Col(sequence_delay_input, width=6),
                                        ]
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            ),
        ]
    )

    return exposure_card
