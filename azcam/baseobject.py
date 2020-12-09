"""
Base main object class.
Only used by other base object classes.
"""

import typing

import azcam


class Objects(object):
    """
    Base class used by main objects (controller, instrument, telescope, etc.).

    Attributes:
        self.id (str): name used to reference the object (controller, display, ...)
        self.name (str): descriptive name for the object
        self.enabled (bool): True (default) when object is enabled
        self.initialized (bool): True when object has been initialized
        self.is_reset (bool): True when object has been reset
    """

    def __init__(self, obj_id: str, obj_name: str = None):
        """
        Args:
            obj_id: name used to reference the object (controller, display, ...)
            obj_name: descriptive name for the object
        """

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
        Reset the object.
        """

        self.is_reset = 1

        return

    def get(self, name: str) -> typing.Any:
        """
        Returns an existing attribute of this class.
        Args:
            name: name of attribute to return
        Returns:
            value: value of attribute or None if not defined
        """

        if not hasattr(self, name):
            return

        attr = getattr(self, name)

        return attr

    def set(self, name: str, value: typing.Any):
        """
        Sets an existing attribute value of this class.
        Args:
            name: name of attribute to set
            value: value of attribute to set
        """

        if not hasattr(self, name):
            return

        setattr(self, name, value)

        return

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

    def read_header(self) -> list:
        """
        Returns the current header.
        Returns:
            list of header lines: [Header[]]: Each element Header[i] contains the sublist (keyword, value, comment, and type).
            Example: Header[2][1] is the value of keyword 2 and Header[2][3] is its type.
        """

        # get the header
        header = []
        reply = self.header.get_all_keywords()
        if reply == []:
            return

        for key in reply:
            reply1 = self.get_keyword(
                key
            )  # this calls object's get_keyword to get updated values
            list1 = [key, reply1[0], reply1[1], reply1[2]]
            header.append(list1)

        return header

    def get_keyword(self, keyword: str) -> list:
        """
        Return a keyword value, its comment string, and type.
        Comment always returned in double quotes, even if empty.
        Args:
            keyword: name of keyword
        Returns:
            list of [keyword, comment, type]

        """

        return self.header.get_keyword(keyword)

    def get_all_keywords(self) -> list:
        """
        Return a list of all keyword names.
        Returns:
            list of all keywords
        """

        return self.header.get_all_keywords()

    def set_keyword(
        self,
        keyword: str,
        value: typing.Any,
        comment: str = None,
        typestring: str = None,
    ):
        """
        Set a keyword value, comment, and type.
        Args:
            keyword: keyword
            value: value of keyword
            comment: comment string
            typestring: one of 'str', 'int', or 'float'
        """

        self.header.set_keyword(keyword, value, comment, typestring)

        return

    def delete_keyword(self, keyword):
        """
        Delete a keyword.
        Args:
            keyword: keyword
        """

        self.header.delete_keyword(keyword)

        return

    def get_info(self):
        """
        Returns header info.
        Returns:
            list of header lines: [Header[]]: Each element Header[i] contains the sublist (keyword, value, comment, and type).
            Example: Header[2][1] is the value of keyword 2 and Header[2][3] is its type.
        """

        header = []
        keywords = self.get_all_keywords()

        for key in keywords:
            reply = self.get_keyword(key)
            list1 = [key, reply[0], reply[1], reply[2]]
            header.append(list1)

        return header
