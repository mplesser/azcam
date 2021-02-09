"""
Contains the SendImage class.
"""

from azcam.baseobject import Objects


class SendImage(Objects):
    """
    azcam's baseclass to send an image to a remote image server.
    """

    def __init__(self, obj_id="sendimage", name="SendImage"):

        super().__init__(obj_id, name)

        self.remote_imageserver_host = ""
        self.remote_imageserver_port = 0
        self.remote_imageserver_type = ""
        self.remote_imageserver_filename = ""

    def sendimage(self, filename: str) -> None:
        """
        Send filename to a remote image server.

        Args:
            filename: filename of image to send
        """

        raise NotImplementedError
