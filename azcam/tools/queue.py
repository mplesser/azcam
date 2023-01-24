"""
Contains the Queue class.
"""

import time
from typing import Any, List

import azcam
from azcam.header import Header, ObjectHeaderMethods
from azcam.tools.tools import Tools


class Queue(Tools, ObjectHeaderMethods):
    """
    The base queue tool.
    Usually implemented as the "queue" tool.
    """

    START_CONDITIONS = "start_conditions"
    STOP_CONDITIONS = "stop_conditions"
    NCYCLES = "ncycles"
    STATUS = "status"
    STATE = "state"
    STEPS = "steps"
    ACTIVE = "active"
    NOBS = "nobs"
    NOBS_COMPLETED = "nobs_completed"
    WAIT_COMPLETED = "wait_completed"
    TOOL = "tools"
    COMMAND = "command"

    def __init__(self, tool_id="queue", description=None):

        Tools.__init__(self, tool_id, description)

        azcam.db.tools_init["queue"] = self
        azcam.db.tools_reset["queue"] = self

        # header object
        self.header = Header("Queue")
        self.header.set_header("queue", 3)

        # create data structure
        self.setup()

        return

    def initialize(self):
        """
        Initialize queue.
        """

        self.initialized = 1

        return

    def setup(self):
        """
        Set up the queue data structure.
        """

        self.data = {
            self.START_CONDITIONS: {},
            self.STOP_CONDITIONS: {},
            self.NCYCLES: 0,
            self.STEPS: {
                self.STATUS: "",
                self.STATE: 0,
                self.ACTIVE: 0,
                self.NOBS: 1,
                self.NOBS_COMPLETED: 0,
                self.WAIT_COMPLETED: 0,
                self.TOOL: None,
                self.COMMAND: None,
            },
        }

    def reset(self):
        """
        Reset queue tool.
        """

        # initialize only once
        if not self.initialized:
            self.initialize()

        return

    def start(self):
        """
        Start the queue.
        """

        return

    def stop(self):
        """
        Stop the queue.
        """

        return

    def pause(self):
        """
        Pause the queue.
        """

        return

    def resume(self):
        """
        Resume the queue.
        """

        return
