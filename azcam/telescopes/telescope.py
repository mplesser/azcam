"""
Contains the base Telescope class.
"""

import azcam
from azcam.header import Header


class Telescope(object):
    """
    Base telescope class.
    """

    def __init__(self, obj_id="telescope"):

        #: telescope name
        self.name = ""

        #: telescope ID
        self.obj_id = obj_id

        #: True when telescope object in enabled
        self.enabled = 1
        #: True when telescope object in initialized
        self.initialized = 0

        # keywords for header, list of [keyword, comment, type]
        self.keywords = {}

        # create the temp control Header object
        self.header = Header("Telescope")
        self.header.set_header("telescope", 5)

        # save object
        setattr(azcam.db, obj_id, self)
        azcam.db.cmd_objects[obj_id] = self
        azcam.db.cli_cmds[obj_id] = self

    def initialize(self):
        """
        Initializes the telescope interface.
        """

        if self.initialized:
            return

        if not self.enabled:
            azcam.AzcamWarning("Telescope is not enabled")
            return

        return

    def reset(self):
        """
        Reset telescope object.
        """

        return

    # ***************************************************************************
    # exposure
    # ***************************************************************************

    def exposure_start(self):
        """
        Optional call before exposure starts.
        """

        return

    def exposure_finish(self):
        """
        Optional call after exposure finishes.
        """

        return

    # ***************************************************************************
    # header
    # ***************************************************************************

    def define_keywords(self):
        """
        Sets up instrument header keywords dictionary, if not already defined.
        """

        if len(self.header.keywords) != 0:
            return

        keywords = []

        # add keywords to header
        if keywords:
            for key in self.keywords:
                self.header.set_keyword(
                    key, "", self.header.comments[key], self.header.typestrings[key]
                )

        return

    def read_header(self):
        """
        Reads each keyword in the header and returns the header with the updated values.
        Returns a list of header lists: [[keyword, value, comment, type]].
        """

        header = []
        reply = self.header.get_all_keywords()

        for key in reply:
            reply = self.get_keyword(key)
            if reply is not None:
                list1 = [key, reply[0], reply[1], reply[2]]  # key, value, comment, type
                header.append(list1)

        return header

    def update_header(self):
        """
        Update the header, reading current data.
        Deletes all keywords if the Telescope is not enabled.
        """

        # delete all keywords if not enabled
        if not self.enabled:
            self.header.delete_all_keywords()
            return

        if not self.initialized:
            self.initialize()

        self.define_keywords()

        self.read_header()

        return

    def get_keyword(self, keyword):
        """
        Return a keyword value and its comment.
        Comment always returned in double quotes, even if empty.
        """

        return self.header.get_keyword(keyword)

    def set_keyword(self, keyword, value, comment=None, typestring=None):
        """
        Set a keyword value and comment.
        typestring is one of 'str', 'int', or 'float'.
        """

        self.header.set_keyword(keyword, value, comment, typestring)

        return

    def delete_keyword(self, keyword):
        """
        Delete a keyword.
        """

        self.header.delete_keyword(keyword)

        return
