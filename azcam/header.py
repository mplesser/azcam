"""
Contains the Header and System classes.
"""

import os
import typing

import azcam
import azcam.utils
import azcam.exceptions


class Header(object):
    """
    Defines the Header class which is used to create and manipulate headers contained
    in many azcam tools.

    Attributes:
        self.title (str): header title dictionary {index:title_line}
        self.keywords (dict): header keywords dictionary {keyword:keywordstring}
        self.values (dict):  header values dictionary {keyword:value}
        self.comments (dict):  header comments dictionary {keyword:comment}
        self.typestrings (dict):  header typestrings dictionary {keyword:typestring)
        self.items (list):  list of header objects
    """

    def __init__(self, title: str = "", template: str | None = None):
        """
        Create instance.

        Args:
            title: title of header to be used in image header
            template: filename of template file with static header info
        """

        self.title = {}  # header title dictionary {index:title_line}
        self.keywords = {}  # header keywords dictionary {keyword:keywordstring}
        self.values = {}  # header values dictionary {keyword:value}
        self.comments = {}  # header comments dictionary {keyword:comment}
        self.typestrings = {}  # header typestrings dictionary {keyword:typestring)
        self.items = []  # list of header objects

        self.filename = ""  # image header filename

        if title != "":
            self.set_title(title)

        if template is not None:
            azcam.db.tools["exposure"].imageheaderfile = template
            self.read_file(template)

    def set_header(self, object_name: str, order: int = -1):
        """
        Sets object_name in the global header dictionary.
        order defines how headers are written in image files.

        Args:
            object_name: name of header object
            order: order to be shown in image header (-1 next)
        """

        if object_name not in list(
            azcam.db.headers.keys()
        ):  # do not change order if already exists
            if order == -1:
                azcam.db.headerorder.append(object_name)
            else:
                azcam.db.headerorder.insert(order, object_name)

        azcam.db.headers[object_name] = self  # may replace an existing object

        return

    def set_title(self, title):
        """
        Set the title of the header.
        """

        # special case
        title = "AzCam Focal plane" if title == "Focalplane" else title
        self.title[0] = (
            "=================================================================="
        )
        self.title[1] = f"{title}"
        self.title[2] = (
            "=================================================================="
        )

        return

    def copy_all_items(self, ptr_header):
        """
        Copy all items from the specified header object to the current image header.
        """

        self.items.append(ptr_header)

        return

    def delete_all_items(self):
        """
        Delete all header items
        """

        self.items = []

        return

    def get_keywords(self):
        """
        Return a list of all keyword names.
        Returns:
            keywords: list of all keywords
        """

        if len(self.keywords) > 0:
            klist = list(self.keywords.keys())
            klist.sort()
        else:
            klist = []

        return klist

    def set_keyword(
        self,
        keyword: str,
        value: typing.Any,
        comment: str | None = None,
        typestring: str | None = None,
    ):
        """
        Set a keyword value, comment, and type.
        Args:
            keyword: keyword
            value: value of keyword
            comment: comment string
            typestring: one of 'str', 'int', or 'float'
        """

        if keyword not in self.keywords:
            self.keywords[keyword] = keyword
            self.values[keyword] = None

        if isinstance(value, str):
            value = value.strip()

        if typestring is None:
            if self.typestrings.get(keyword) is None:
                self.typestrings[keyword] = "str"
        else:
            self.typestrings[keyword] = typestring

        if value is not None:
            if self.typestrings[keyword] == "str":
                value = str(value)
            elif self.typestrings[keyword] == "int":
                value = int(value)
            elif self.typestrings[keyword] == "float":
                value = float(value)
        self.values[keyword] = value

        if comment is None or comment == "none":
            if self.comments.get(keyword):  # use previous comment
                pass
            else:
                self.comments[keyword] = ""
        else:
            self.comments[keyword] = comment

        return

    def set_keyword_string(self, keystring):
        """
        Set keyword data from a single string.
        """

        keystring = keystring.strip()
        if len(keystring) == 0:
            return

        # allow for quotes
        tokens = azcam.utils.parse(keystring)

        keyword = tokens[0]

        # find comment after '/'
        comment = ""
        value = ""
        for i, t in enumerate(tokens):
            if t == "/":
                comment = " ".join(tokens[i + 1 :])
                value = " ".join(tokens[1:i])

        if comment == "":
            value = " ".join(tokens[1:])

        # try to get type of value
        t = "str"
        if isinstance(value, int):
            value = int(value)
            t = "int"
        elif isinstance(value, float):
            value = float(value)
            t = "float"

        self.set_keyword(keyword, value, comment, t)

        return

    def get_keyword(self, keyword: str) -> list:
        """
        Return a keyword value, its comment string, and type.
        Comment always returned in double quotes, even if empty.
        Args:
            keyword (str): name of keyword
        Returns:
            list of [keyword, comment, type]
        """

        value = self.values[keyword]
        comment = self.comments[keyword]
        if comment is None:
            comment = ""
        t = self.typestrings[keyword]

        return [value, comment, t]

    def delete_keyword(self, keyword: str):
        """
        Delete a keyword.
        """

        try:
            del self.keywords[keyword]
        except KeyError:
            pass
        try:
            del self.values[keyword]
        except KeyError:
            pass
        try:
            del self.comments[keyword]
        except KeyError:
            pass

        return

    def delete_all_keywords(self):
        """
        Delete all keywords.
        """

        keys = self.get_keywords()
        for key in keys:
            self.delete_keyword(key)  # delete in header

        return

    def get_string(self):
        """
        Returns the entire header as a single formatted string.
        """

        lines = ""

        header = self.get_header()
        for telem in header:
            line = telem[0] + " " + str(telem[1]) + " " + str(telem[2]) + "\n"
            lines += line

        return lines

    def convert_type(self, value, pythontype):
        """
        Convert a value to a specific type.
        """

        if pythontype == "str" or pythontype not in ["int", "float"]:
            typestring = "str"
            value = str(value)
        elif pythontype == "int":
            typestring = "int"
            value = int(value)
        else:
            typestring = "float"
            value = float(value)

        return value, typestring

    def update(self):
        """
        Update header.
        """

        return

    def get_header(self) -> list:
        """
        Returns the header list.
        Returns:
            list of header lines: [Header[]]: Each element contains (keyword,value,comment,type).
        """

        # get the header
        header = []
        reply = self.get_keywords()
        if reply == []:
            return header

        for key in reply:
            reply1 = self.get_keyword(key)
            list1 = [key, reply1[0], reply1[1], reply1[2]]
            header.append(list1)

        return header

    def read_file(self, filename=""):
        """
        Read a header file and import the data into the header.
        """

        # if no file specified, just skip
        if filename == "":
            return

        if not os.path.exists(filename):
            azcam.exceptions.AzcamError(f"Header file not found: {filename}")

        with open(filename, "r") as f1:
            for line in f1.readlines():
                line = line.rstrip()
                line = line.lstrip()
                if line.startswith("#"):
                    continue
                if len(line) == 0:
                    continue
                tokens = line.split(" ", 1)
                keyword = tokens[0]

                if keyword == "COMMENT" and len(tokens) == 1:
                    value = ""
                    comment = ""
                else:
                    nslash = tokens[1].find("/")
                    if nslash == -1:
                        value = tokens[1].strip()
                        comment = ""
                    else:
                        comment = tokens[1][nslash + 1 :].strip()
                        value = tokens[1][:nslash].strip()

                typ, val = azcam.utils.get_datatype(value)
                self.set_keyword(keyword, val, comment, typ)

        self.filename = filename

        return


class ObjectHeaderMethods(object):
    """
    Header methods for main objects.
    These are called like "controller.get_keyword()".
    """

    def __init__(self) -> None:
        pass

    def define_keywords(self):
        """
        Defines and resets keywords.
        """

        return

    def update_header(self):
        """
        Update the header, reading current data.
        Deletes all keywords if the object is not enabled.
        """

        if not self.is_enabled:
            self.header.delete_all_keywords()
            return

        if not self.is_initialized:
            self.initialize()

        self.define_keywords()

        self.read_header()

        return

    def read_header(self) -> list:
        """
        Reads and returns current header data.
        Returns:
            list of header lines: [Header[]]: Each element contains (keyword,value,comment,type).
        """

        # Example: Header[2][1] is the value of keyword 2 and Header[2][3] is its type.

        # get the header
        header = []
        reply = self.header.get_keywords()
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

    def get_keywords(self) -> list:
        """
        Return a list of all keyword names.
        Returns:
            keywords: list of all keywords
        """

        return self.header.get_keywords()

    def set_keyword(
        self,
        keyword: str,
        value: typing.Any,
        comment: str = "none",
        typestring: str = "none",
    ):
        """
        Set a keyword value, comment, and type.
        Args:
            keyword: keyword
            value: value of keyword
            comment: comment string
            typestring: one of 'str', 'int', or 'float'
        """

        # if typestring == "none":
        #     typestring = None
        # if comment == "none":
        #     comment = None

        self.header.set_keyword(keyword, value, comment, typestring)

        return

    def delete_keyword(self, keyword: str):
        """
        Delete a keyword.
        Args:
            keyword: keyword
        """

        self.header.delete_keyword(keyword)

        return


class System(ObjectHeaderMethods):
    """
    System class.
    """

    def __init__(self, system_name, template_file=None):
        self.header = Header(system_name, template_file)
        self.header.set_header("system", 0)

        self.system = self

        return
