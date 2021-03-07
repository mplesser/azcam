"""
API for remote interfaces.
Currently support command strings from command server and web server.
"""

from urllib.parse import urlparse

from flask import jsonify

import azcam


class API(object):
    """
    API for azcam remote services.
    """

    def __init__(self) -> None:
        self.default_tool = None

    def string_command(self, command: str, **kwargs):
        """
        Parse and execute a command string.
        Returns the reply string, always starting with OK or ERROR.
        Traps all errors.
        """

        # parse command string
        tokens = azcam.utils.parse(command, 0)
        cmd = tokens[0]

        # command must be of form tool.command
        if ("." in cmd) or (self.default_tool is not None):

            if "." in cmd:
                cmdobject, cmdcommand = cmd.split(".")
            else:
                cmdobject = self.default_tool
                cmdcommand = cmd

            if cmdobject not in azcam.db.remote_tools:
                s = f"remote access to {cmdobject} is not allowed"
                azcam.AzcamWarning(s)
                return f"ERROR {s}"

            cmd = getattr(azcam.db, cmdobject)
            cmd = getattr(cmd, cmdcommand)
            kwargs = {}
            l1 = len(tokens)
            if l1 > 1:
                args = tokens[1:]
                if "=" in args[0]:
                    # assume all keywords for now
                    kwargs = {}
                    for argtoken in args:
                        keyword, value = argtoken.split("=")
                        kwargs[keyword] = value
                    args = []
            else:
                args = []
            reply = cmd(*args, **kwargs)  # execute
        else:
            s = f"command not recognized: {cmd} "
            azcam.AzcamWarning(s)
            return s

        # process reply
        if reply is None or reply == "":
            s = ""

        elif type(reply) == str:
            s = reply

        elif type(reply) == list:
            s = ""
            for x in reply:
                if type(x) == str and " " in x:  # check if space in the string
                    s = s + " " + "'" + str(x) + "'"
                else:
                    s = s + " " + str(x)
            s = s.strip()

        else:
            s = repr(reply)

            if s != '""':
                s = s.strip()

        # add OK status if needed
        if not (s.startswith("OK") or s.startswith("ERROR") or s.startswith("WARNING")):
            s = "OK " + s

        s = s.strip()

        return s

    def web_command(self, command, url):
        """
        Parse a web URL and make call to proper tool method, returning reply.
        """

        try:
            caller, kwargs = self.webparse(url)
            reply = caller() if kwargs is None else caller(**kwargs)

        except azcam.AzcamError as e:
            azcam.log(f"web_command error: {e}")
            if e.error_code == 4:
                reply = "remote call not allowed"
            else:
                reply = f"web_command error: {repr(e)}"
        except Exception as e:
            azcam.log(e)
            reply = f"invalid API command: {url}"

        webreply = self.make_response(command, reply)

        return webreply

    def webparse(self, url):
        """
        Parse URL.
        """

        s = urlparse(url)
        p = s.path[5:]  # remove /api/
        # p = s.path[1:]

        try:
            tokens = p.split("/")
        except Exception as e:
            raise e("Invalid API command")

        obj, method = tokens[:2]
        args = s.query.split("&")

        if args == [""]:
            kwargs = None
        else:
            kwargs = {}
            for arg1 in args:
                arg, par = arg1.split("=")
                kwargs[arg] = par

        try:
            objid = getattr(azcam.db, obj)
        except Exception:
            raise azcam.AzcamError(f"remote call not allowed in API: {obj}", 4)

        caller = getattr(objid, method)

        return caller, kwargs

    def make_response(self, command, reply):

        # generic response
        response = {
            "message": "Finished",
            "command": command,
            "data": reply,
        }

        response = jsonify(response)

        return response


api = API()
setattr(azcam.db, "api", api)
azcam.db.cli_tools["api"] = api
