from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc

import azcam


def filename_card():
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
        azcam.db.webserver.set_message(value)
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
        try:
            azcam.db.parameters.set_par("imagesequencenumber", seqnum)
            azcam.db.parameters.set_par("imageroot", root)
            azcam.db.parameters.set_par("imagefolder", folder)
        except Exception as e:
            print(e)
        return

    filename_card = dbc.Card(
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

    return filename_card
