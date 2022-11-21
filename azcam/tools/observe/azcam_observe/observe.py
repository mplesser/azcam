"""
Contains the Observe class for Qt and CLI usage.
"""

from azcam.tools.tools import Tools
from azcam_observe.observe_qt.observe_qt import ObserveQt
from azcam_observe.observe_cli.observe_cli import ObserveCli


class Observe(Tools, ObserveQt, ObserveCli):
    """
    The common Observe class for both Qt and CLI usage.
    """

    def __init__(self):

        Tools.__init__(self, "observe")

        ObserveQt.__init__(self)
        ObserveCli.__init__(self)
