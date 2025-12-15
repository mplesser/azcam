from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc

import azcam


def status_card():
    """
    Create status card.
    """
    # status card
    style1 = {"font-style": "italic"}

    row1 = html.Tr(
        [
            html.Td("Image Filename", style=style1),
            html.Td("filename here", id="filename_status", colSpan=3),
        ]
    )
    row2 = html.Tr(
        [
            html.Td("Image Title", style=style1),
            html.Td("title here", id="imagetitle_status", colSpan=3),
        ]
    )
    row3 = html.Tr(
        [
            html.Td("Image Type", style=style1),
            html.Td("type here", id="imagetype_status"),
            html.Td("Exposure Time", style=style1),
            html.Td("ET here", id="et_status"),
        ]
    )
    row4 = html.Tr(
        [
            html.Td("Test Image", style=style1),
            html.Td("test here", id="imagetest_status"),
            html.Td("Mode", style=style1),
            html.Td("mode here", id="mode_status"),
        ]
    )
    row5 = html.Tr(
        [
            html.Td("Temperatures", style=style1),
            html.Td("temps here", id="temps_status"),
            html.Td("Binning", style=style1),
            html.Td("binning here", id="binning_status"),
        ]
    )
    row_messsage = html.Tr(
        [
            html.Td("Message", style=style1),
            html.Td("messages here", id="message_status", colSpan=3),
        ]
    )
    row_ts = html.Tr(
        [
            html.Td("Timestamp", style=style1),
            html.Td("timestamp here", id="timestamp_status", colSpan=3),
        ]
    )
    row_progress = html.Tr(
        [
            html.Td("Progress", style=style1),
            html.Td(
                dbc.Progress(id="progress_status"),
                colSpan=3,
            ),
        ]
    )

    table_body = [
        html.Tbody([row1, row2, row3, row4, row5, row_progress, row_ts, row_messsage])
    ]
    table = dbc.Table(
        table_body,
        bordered=True,
        striped=True,
        # dark=False,
        style={"padding": "2em"},
    )
    # table = dbc.Table(table_header + table_body, bordered=True)

    status_card = dbc.Card(
        [
            dbc.CardHeader(
                "Status for Current Exposure", style={"font-weight": "bold"}
            ),
            dbc.CardBody(
                [
                    html.Div(
                        "",
                        id="estate_status",
                        style={"font-weight": "bold"},
                    ),
                    table,
                ]
            ),
        ]
    )

    # status table update
    @callback(
        Output("filename_status", "children"),
        Output("imagetitle_status", "children"),
        Output("imagetype_status", "children"),
        Output("et_status", "children"),
        Output("imagetest_status", "children"),
        Output("mode_status", "children"),
        Output("temps_status", "children"),
        Output("binning_status", "children"),
        Output("timestamp_status", "children"),
        Output("estate_status", "children"),
        Output("progress_status", "value"),
        Output("message_status", "children"),
        Input("expstatus_interval", "n_intervals"),
    )
    def update_expstatus(n):
        """
        Get exposure status and update fields.
        """

        webdata = azcam.db.tools["exposure"].get_status()

        # the return order must match Output order
        filename = webdata["filename"]
        imagetitle = webdata["imagetitle"]
        imagetype = webdata["imagetype"]
        et = webdata["exposuretime"]
        imagetest = webdata["imagetest"]
        mode = webdata["mode"]

        camtemp = float(webdata["camtemp"])
        dewtemp = float(webdata["dewtemp"])
        temps = f"Camera: {camtemp:.01f} C    Dewar: {dewtemp:.01f} C"

        colbin = webdata["colbin"]
        rowbin = webdata["rowbin"]
        binning = f"RowBin: {rowbin}    ColBin: {colbin}"

        ts = webdata["timestamp"]
        estate = webdata["exposurestate"]
        progress = float(webdata["progressbar"])
        message = webdata["message"]

        return [
            filename,
            imagetitle,
            imagetype,
            et,
            imagetest,
            mode,
            temps,
            binning,
            ts,
            estate,
            progress,
            message,
        ]

    return status_card
