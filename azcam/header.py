"""
Contains the Header class.
"""

import os

import azcam


class Header(object):
    """
    Defines the Header class which is used to create and manipulate headers contained
    in azcam objects such as *controller* and *instrument*.
    """

    def __init__(self, title: str = "", template=None):

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
            azcam.api.exposure.imageheaderfile = template
            self.read_file(template)

    def set_header(self, object_name, order=-1):
        """
        Sets object_name in the global header dictionary.
        order defines how headers are written in image files.
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
        title = "ITL Focal plane" if title == "Focalplane" else title
        self.title[
            0
        ] = "=================================================================="
        self.title[1] = "%s" % title
        self.title[
            2
        ] = "=================================================================="

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

    def get_all_keywords(self):
        """
        Return a list of all keyword names.
        """

        klist = list(self.keywords.keys())
        klist.sort()

        return klist

    def define_keywords(self, keywords=[], comments={}, typestrings={}):
        """
        Defines keywords, if they are not already defined.
        """

        if len(self.keywords) != 0:
            return

        if len(keywords) > 0:
            for key in keywords:
                self.set_keyword(key, "", comments[key], typestrings[key])

        return

    def set_keyword(self, keyword, value, comment=None, typestring=None):
        """
        Set a keyword value and comment.
        typestring is one of 'str', 'int', or 'float'.
        """

        if keyword not in self.keywords:
            self.keywords[keyword] = keyword

        if type(value) == str:
            value = value.strip()

        self.values[keyword] = value

        if comment is None:
            if self.comments.get(keyword):  # use previous comment
                pass
            else:
                self.comments[keyword] = ""
        else:
            self.comments[keyword] = comment

        if typestring is None:
            self.typestrings[keyword] = self.get_type_string(str)  # assume string
        else:
            self.typestrings[keyword] = typestring

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
        t = self.get_type_string(str)  # default
        if type(value) == int:
            value = int(value)
            t = self.get_type_string(int)
        elif type(value) == float:
            value = float(value)
            t = self.get_type_string(float)

        self.set_keyword(keyword, value, comment, t)

        return

    def get_keyword(self, keyword):
        """
        Return a keyword value and its comment.
        Comment always returned in double quotes, even if empty.
        """

        value = self.values[keyword]
        comment = self.comments[keyword]
        if comment is None:
            comment = ""
        t = self.get_type_string(self.typestrings[keyword])

        return [value, comment, t]

    def delete_keyword(self, keyword):
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

        keys = self.get_all_keywords()
        for key in keys:
            self.delete_keyword(key)  # delete in header

        return

    def get_info(self):
        """
        Returns header info.
        Returns [Header[]]: Each element Header[i] contains the sublist (keyword, value, comment, and type).
        Example: Header[2][1] is the value of keyword 2 and Header[2][3] is its type.
        """

        header = []
        keywords = self.get_all_keywords()

        for key in keywords:
            reply = self.get_keyword(key)
            list1 = [key, reply[0], reply[1], reply[2]]
            header.append(list1)

        return header

    def get_string(self):
        """
        Returns the entire header as a single formatted string.
        """

        lines = ""

        header = self.get_info()
        for telem in header:
            line = telem[0] + " " + str(telem[1]) + " " + str(telem[2]) + "\n"
            lines += line

        return lines

    def get_type_string(self, pythontype):
        """
        Make a string indicating the python data type pythontype.
        """

        if pythontype == str or pythontype not in [int, float]:
            attributetypestring = "str"
        elif pythontype == int:
            attributetypestring = "int"
        else:
            attributetypestring = "float"

        return attributetypestring

    def convert_type(self, value, pythontype):
        """
        Convert a value to a specific type.
        """

        if pythontype == str or pythontype not in [int, float]:
            typestring = "str"
            value = str(value)
        elif pythontype == int:
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

    def read_file(self, filename=""):
        """
        Read a header file and import the data into the header.
        """

        # if no file specified, just skip
        if filename == "":
            return

        if not os.path.exists(filename):
            azcam.AzcamWarning("Header file not found:%s" % filename)
            return

        with open(filename, "r") as f1:
            for line in f1.readlines():
                line = line.rstrip()
                line = line.lstrip()
                if line.startswith("#"):
                    break
                if len(line) == 0:
                    break
                tokens = line.split(" ", 1)
                keyword = tokens[0]

                if keyword == "COMMENT" and len(tokens) == 1:
                    value = ""
                    comment = ""
                else:
                    tokens = tokens[1].split("/")
                    value = tokens[0].strip()
                    comment = tokens[1].strip() if len(tokens) > 1 else ""
                self.set_keyword(keyword, value, comment, type(value))

        self.filename = filename

        return
