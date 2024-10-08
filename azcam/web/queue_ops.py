import time
import base64
import datetime
import io

from dash import html, dcc, callback, Input, Output, State, dash_table
import pandas as pd

import azcam


def execute():
    """
    Execute queue dataframe.
    """

    df = azcam.db.queue_df

    for irow in df.index:
        azcam.db.queueserver.set_message(f"Executing script row {irow}")
        cmd = df.iloc[irow]["Command"]

        if cmd.startswith("print"):
            text = cmd.lstrip("print ")
            azcam.db.queueserver.set_message(f"{text}")

        elif cmd.startswith("delay"):
            delay = float(cmd.lstrip("delay "))
            azcam.db.queueserver.set_message(f"Delaying {delay} secs")
            time.sleep(delay)

        elif cmd.startswith("movefilter"):
            filt = cmd.lstrip("movefilter ")
            azcam.db.queueserver.set_message(f"Moving filte to {filt}")

        elif cmd.startswith("steptel"):
            ra_dec = cmd.lstrip("steptel ")
            azcam.db.queueserver.set_message(f"Stepping telescope by {ra_dec}")

        elif cmd.startswith("movetel"):
            ra_dec = cmd.lstrip("movetel ")
            azcam.db.queueserver.set_message(f"Moving telescope {ra_dec}")

        elif cmd.startswith("epoch"):
            epoch = float(cmd.lstrip("epoch "))
            azcam.db.queueserver.set_message(f"Epoch is {epoch}")

        time.sleep(0.5)

    return


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
