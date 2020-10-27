"""
Base main object class.
Only used by other base object classes.
"""

import azcam


class Objects(object):
    """
    Base class used by main objects (controller, instrument, telescope, etc.).
    """

    def __init__(self, obj_id, obj_name=None):

        #: id is the name used to reference the object (controller, display, ...)
        self.id = obj_id

        #: name is a descriptive name for the object
        self.name = obj_name

        #: True when object is enabled
        self.enabled = 1

        #: True when object has been initialized
        self.initialized = 0

        # True when object has been reset
        self.is_reset = 0

        # add object to api and cli_cmds
        setattr(azcam.api, self.id, self)
        azcam.db.cli_cmds[self.id] = self

    def initialize(self):
        """
        Initialize the object.
        """

        if self.initialized:
            return

        if not self.enabled:
            azcam.AzcamWarning(f"{self.name} is not enabled")
            return

        self.initialized = 1

        return

    def reset(self):
        """
        Reset object.
        """

        self.is_reset = 1

        return

    # ****************************************************************
    # header
    # ****************************************************************
    def define_keywords(self):
        """
        Sets up header keywords dictionary if not already defined.
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

    def update_header(self):
        """
        Update the header, reading current data.
        Deletes all keywords if the object is not enabled.
        """

        if not self.enabled:
            self.header.delete_all_keywords()
            return

        if not self.initialized:
            self.initialize()

        self.define_keywords()

        self.read_header()

        return

    def read_header(self):
        """
        Returns the current header.
        Returns [Header[]]: Each element Header[i] contains the sublist (keyword, value, comment, and type).
        Example: Header[2][1] is the value of keyword 2 and Header[2][3] is its type.
        """

        # get the header
        header = []
        reply = self.header.get_all_keywords()

        for key in reply:
            reply1 = self.get_keyword(
                key
            )  # this calls object's get_keyword to get updated values
            list1 = [key, reply1[0], reply1[1], reply1[2]]
            header.append(list1)

        return header

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
