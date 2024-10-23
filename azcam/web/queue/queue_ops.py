import time

import azcam


def execute():
    """
    Execute queue dataframe.
    """

    df = azcam.db.queue_df

    for irow in df.index:
        print(f"Row {irow}")
        cmd = df.iloc[irow]["Command"]

        if cmd.startswith("print"):
            text = cmd.lstrip("print ")
            print(f" {text}")

        elif cmd.startswith("delay"):
            delay = float(cmd.lstrip("delay "))
            print(f" Delay {delay} secs")
            time.sleep(delay)

        elif cmd.startswith("movefilter"):
            filt = cmd.lstrip("movefilter ")
            print(f" Moving filter to {filt}")

        elif cmd.startswith("steptel"):
            ra_dec = cmd.lstrip("steptel ")
            print(f" Stepping telescope to {ra_dec}")

        elif cmd.startswith("movetel"):
            ra_dec = cmd.lstrip("movetel ")
            print(f" Moving telescope to {ra_dec}")

        time.sleep(0.5)

    return
