from dash import Dash, html, dcc, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import dash_daq as daq

import azcam


def tabs_buttons():

    buttons = dbc.ButtonGroup(
        [
            dbc.Button("Exposure", id="exposure_tab_btn", className="me-1", n_clicks=0),
            dbc.Button("Filename", id="filename_tab_btn", className="me-1", n_clicks=0),
            dbc.Button("Detector", id="detector_tab_btn", className="me-1", n_clicks=0),
            dbc.Button("Options", id="options_tab_btn", className="me-1", n_clicks=0),
        ],
        vertical=False,
    )

    @callback(
        Output("tabs", "active_tab", allow_duplicate=True),
        Output("image_type_dropdown", "value"),
        Output("title_input", "value"),
        Output("test_image", "value"),
        Output("et", "value"),
        Output("seq_num", "value"),
        Output("seq_delay", "value"),
        Input("exposure_tab_btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def on_button_click_exposure_tab_btn(n):
        exposure = azcam.db.tools["exposure"]
        image_type_dropdown = exposure.get_image_type()
        title_input = exposure.get_image_title()
        test_image = exposure.test_image
        et = exposure.exposure_time
        seq_num = exposure.exposure_sequence_total
        seq_delay = exposure.exposure_sequence_delay
        return [
            "exposure_tab",
            image_type_dropdown,
            title_input,
            test_image,
            et,
            seq_num,
            seq_delay,
        ]

    @callback(
        Output("tabs", "active_tab", allow_duplicate=True),
        Output("folderselect", "value"),
        Output("rootselect", "value"),
        Output("seqnumselect", "value"),
        Input("filename_tab_btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def on_button_click_filename_tab_btn(n):
        exposure = azcam.db.tools["exposure"]
        seq = exposure.sequence_number
        folder = exposure.folder
        root = exposure.root

        return ["filename_tab", folder, root, seq]

    @callback(
        Output("tabs", "active_tab", allow_duplicate=True),
        Output("first_col", "value"),
        Output("last_col", "value"),
        Output("col_bin", "value"),
        Output("first_row", "value"),
        Output("last_row", "value"),
        Output("row_bin", "value"),
        Input("detector_tab_btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def on_button_click_detector_tab_btn(n):
        firstcol, lastcol, firstrow, lastrow, colbin, rowbin = azcam.db.tools[
            "exposure"
        ].get_roi()

        return [
            "detector_tab",
            firstcol,
            lastcol,
            colbin,
            firstrow,
            lastrow,
            rowbin,
        ]

    @callback(
        Output("tabs", "active_tab", allow_duplicate=True),
        Output("flush_sensor", "value"),
        Output("display_image", "value"),
        Output("enable_instrument", "value"),
        Output("enable_telescope", "value"),
        Output("auto_title", "value"),
        Input("options_tab_btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def on_button_click_options_tab_btn(n):
        flush_sensor = azcam.db.tools["exposure"].flush_array
        display_image = azcam.db.tools["exposure"].display_image
        enable_instrument = azcam.db.tools["instrument"].is_enabled
        enable_telescope = azcam.db.tools["telescope"].is_enabled
        auto_title = azcam.db.tools["exposure"].auto_title

        return [
            "options_tab",
            flush_sensor,
            display_image,
            enable_instrument,
            enable_telescope,
            auto_title,
        ]

    return buttons


def tabs(parent):

    exposure_tab = [
        dbc.CardBody(
            [
                parent.exposure_card,
                parent.status_card,
            ]
        )
    ]

    filename_tab = [
        parent.filename_card,
        html.Div(id="filename_out"),
    ]

    detector_tab = [
        parent.detector_card,
    ]

    options_tab = [
        parent.options_card,
    ]

    tabs = dbc.Tabs(
        [
            dbc.Tab(exposure_tab, tab_id="exposure_tab"),
            dbc.Tab(filename_tab, tab_id="filename_tab"),
            dbc.Tab(detector_tab, tab_id="detector_tab"),
            dbc.Tab(options_tab, tab_id="options_tab"),
        ],
        id="tabs",
        active_tab="exposure_tab",
    )

    # @callback(
    #     Output("folderselect", "value"),
    #     Output("rootselect", "value"),
    #     Output("seqnumselect", "value"),
    #     Input("tabs", "active_tab"),
    # )
    # def switch_tab(at):

    #     exposure = azcam.db.tools["exposure"]
    #     if at == "exposure_tab":
    #         return ["", "", 99]
    #     elif at == "filename_tab":
    #         seq = exposure.sequence_number
    #         folder = exposure.folder
    #         root = exposure.root
    #         return [folder, root, seq]
    #     elif at == "detector_tab":
    #         return ["", "", 99]
    #     elif at == "options_tab":
    #         return ["", "", 99]
    #     else:
    #         return ["", "", 99]

    return tabs
