"""
Contains the Queue class.
"""

import time
from collections import OrderedDict

import azcam
from azcam.header import Header, ObjectHeaderMethods
from azcam.tools.tools import Tools


class Queue(Tools, ObjectHeaderMethods):
    """
    The base queue tool.
    Usually implemented as the "queue" tool.
    """

    def __init__(self, tool_id="queue", description=None):

        Tools.__init__(self, tool_id, description)

        azcam.db.tools_init["queue"] = self
        azcam.db.tools_reset["queue"] = self

        # header object
        self.header = Header("Queue")
        self.header.set_header("queue", 3)

        # create data structure
        self.START_CONDITIONS = {}
        self.STOP_CONDITIONS = {}
        self.NCYCLES = 0
        self.NCYCLES_COMPLETED = 0
        self.QUEUE_STATUS = ""
        self.STEPS = []  # list of steps, each step is a dict

        self.STATUS = ""
        self.START_CONDITIONS: {}
        self.STOP_CONDITIONS: {}

        self.setup()

        return

    def setup(self):
        """
        Set up the queue data structure.
        """

        self.data = {
            "START_CONDITIONS": {},
            "STOP_CONDITIONS": {},
            "NCYCLES": 0,
            "NCYCLES_COMPLETED": 0,
            "QUEUE_STATUS": "",

            # self.STEPS: {
            #     "STATUS": "",
            #     "ACTIVE": 0,
            #     "NOBS": 1,
            #     "NOBS_COMPLETED": 0,
            #     "WAIT_FLAG": 0,
            #     "TOOL": None,
            #     "COMMAND": None,
            # },
        }

        # debug
        if 1:
            self.mock_setup()

    def initialize(self):
        """
        Initialize queue.
        """

        self.initialized = 1

        return

    def mock_setup(self):
        """
        Set up mock data for queue testing.
        """

        # self.data = {
        #     self.START_CONDITIONS: {},
        #     self.STOP_CONDITIONS: {},
        #     self.NCYCLES: 0,
        #     self.NCYCLES_COMPLETED: 0,
        #     self.STEPS: {
        #         self.STATUS: "",
        #         self.ACTIVE: 0,
        #         self.NOBS: 1,
        #         self.NOBS_COMPLETED: 0,
        #         self.WAIT_FLAG: 0,
        #         self.TOOL: None,
        #         self.COMMAND: None,
        #     },
        # }

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
