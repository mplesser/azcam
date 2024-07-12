import time


class ObsTime(object):
    """
    Defines the ObsTime class.
    Used by the exposure tool.
    """

    def __init__(self):

        # UT
        self.utc = []
        # UT date only
        self.date = []
        # UT time only
        self.ut = []
        # local time
        self.local_time = []
        # local time zone
        self.time_zone = []
        # time system
        self.time_system = []

        return

    def update(self, index=0):
        """
        Save the current time parameters into the specified internal index.
        Index is 0 for open shutter time.
        """

        if len(self.utc) < index + 1:
            self.utc.append("")
            self.date.append("")
            self.ut.append("")
            self.local_time.append("")
            self.time_zone.append("")
            self.time_system.append("")

        # get current time and date
        gmt = time.gmtime()
        self.utc[index] = str(gmt[0]) + time.strftime("-%m-%d", gmt)

        self.date[index] = self.utc[index]

        t = time.time()
        fracsec = int(1000 * round(t - int(t), 3))
        self.ut[index] = time.strftime("%H:%M:%S.", gmt) + "%.3u" % fracsec

        self.time_zone[index] = time.timezone / 3600

        self.local_time[index] = time.strftime("%H:%M:%S", time.localtime())

        self.time_system[index] = "UTC"

        return
