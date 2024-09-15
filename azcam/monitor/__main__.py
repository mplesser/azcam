"""
Starts the azcammonitor application.
This runs from a dedicated azcamconsole.
"""

import threading

from azcam.monitor.azcammonitor import AzCamMonitor


def main():
    """
    Starts azcammonitor.
    Usage examples:
      python -m azcam.monitor
      ipython -m azcam.monitor --
    """

    # start process
    azcammonitor = AzCamMonitor()
    azcammonitor.load_configfile()
    azcammonitor.start_udp_server()
    azcammonitor.start_watchdog()

    # run in a thread to allow inspection
    if 0:
        thread = threading.Thread(
            target=azcammonitor.start_webserver, name="monitorserver"
        )
        thread.start()
    else:
        azcammonitor.start_webserver()

    # return azcammonitor
    return


if __name__ == "__main__":
    azcammonitor = main()
