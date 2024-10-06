import time

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
