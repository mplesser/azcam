import os


class Filename(object):
    """
    Filename class used to manipulate image filenames.
    Used by the exposure tool.
    """

    def __init__(self, parent=None):
        """
        Creates a filename instance.

        param object parent: reference to parent image object
        """

        # self.parent = parent  # calling object reference
        self.parent = self  # calling object reference

        self.filetype = 0  # from image object
        # True to overwrite image files of the same name
        self.overwrite = 0
        # current image file folder
        self.folder = ""
        # current image file root name
        self.root = "a."
        # current image file sequence number
        self.sequence_number = 1
        # True to increment file sequence number after each exposure
        self.auto_increment_sequence_number = 0
        # True to include file sequence number in each image name
        self.include_sequence_number = 0
        # True to automatically name image based on imagetype
        self.autoname = 0
        # True when current file is a test image
        self.test_image = 1

        if parent is not None:
            self.filetype = parent.filetype

    def get_filename(self):
        """
        Return current filename as a single string.
        This is the filename for the next exposure to be taken.

        Always uses forward slashes for folder delimiter.
        This name is usually the next image to be produced.
        """

        self.filetype = self.parent.filetype

        folder = self.folder.replace("\\", "/")
        if not folder.endswith("/"):
            folder = folder + "/"

        extension = self.get_extname(self.filetype)

        if self.test_image:
            filename = folder.replace("\\", "/") + "test" + "." + extension
        elif self.include_sequence_number:
            if self.autoname:
                filename = (
                    folder
                    + self.root
                    + "."
                    + self.parent.image_type.upper()
                    + "."
                    + "%04d" % self.sequence_number
                    + "."
                    + extension
                )
            else:
                filename = (
                    folder + self.root + "%04d" % self.sequence_number + "." + extension
                )
        else:
            if self.autoname:
                filename = (
                    folder
                    + self.root
                    + "."
                    + self.parent.image_type.upper()
                    + "."
                    + extension
                )
            else:
                filename = folder + self.root + "." + extension

        filename = filename.replace(
            "..", "."
        )  # clean up as could have two periods together

        return filename

    def set_filename(self, filename: str):
        """
        Set the filename components based on a simple filename.

        Args:
            filename: filename to be set
        """

        self.filetype = self.parent.filetype

        filename = os.path.normpath(filename)
        self.folder = os.path.dirname(filename)
        if self.folder == "":
            self.folder = "./"

        f = os.path.basename(filename)

        # if f.endswith(".fits"):
        #     f = f.replace(".fits", "")
        #     self.filetype = 0

        f = f.split(".")  # root is just first part
        self.root = f[0]

        return

    def increment_filenumber(self):
        """
        Increment the filename sequence number if AutoIncrementSequenceNumber is True and not a test image.
        """

        if self.auto_increment_sequence_number and not self.test_image:
            self.sequence_number += 1

        return

    def get_extname(self, filetype):
        """
        Return the file extension string for a file type.
        """

        if filetype in [0, 1, 6]:
            return "fits"
        elif filetype == 2:
            return "bin"
        elif filetype == 3:
            return "tif"
        elif filetype == 4:
            return "jpg"
        elif filetype == 5:
            return "gif"
        else:
            return ""
