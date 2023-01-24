import glob
import math
import os
import shutil
import warnings

import numpy
import scipy.ndimage
import scipy.ndimage.filters
import scipy.optimize

import azcam
from azcam.tools.testers.basetester import Tester
from astropy.io import fits as pyfits

# constants
CON1 = 2.0 * numpy.sqrt(2.0 * numpy.log(2.0))  # 2.355 for sigma <=> FWHM


class Fe55(Tester):
    """
    Fe55 X-ray signal acquisition and analysis.
    """

    def __init__(self):

        super().__init__("fe55")

        self.ext_analyze = -1  # extension to analyze if not entire image
        self.fit_type = 0

        self.exposure_time = -1
        self.number_images_acquire = -1
        self.dark_correct = 0  # take and use a dark exposure
        self.exposure_type = "fe55"
        self.gain_estimate = []
        self.bin_size = 4
        self.max_images = -1  # limit numbe of image files analyzed
        self.max_events = -1  # limit number events analyzed per channel

        self.acquire_darks = 0  # flag to acquire darks of the same exposur time

        self.number_events = []
        self.pixel_size = -1
        self.spec_sigma = -1  # charge diffusion spec in microns
        self.fit_psf = 0
        self.mean_fwhmTotal = -1
        self.mean_sigmaTotal = -1
        self.num_chans = -1

        self.readnoise_spec = -1
        self.grade_read_noise = "UNKNOWN"
        self.noise_dn = []
        self.read_noise = []
        self.system_noise_correction = []  # camera noise (no sensor) in DN

        # X-ray lines in electrons
        # 25  Mn 5.89875   5.88765   6.49045   KeV
        # self.XrayLines={'K-alpha':1620,'K-beta':1778.}
        # self.XrayLines={'K-alpha':1590}                  # cold per LSST
        self.xray_lines = {"K-alpha": 1615.1}  # cold per LSST 23Oct17

        self.neighborhood_size = 5  # odd number
        self.threshold = 0  # peak of split events for searching
        self.noise_threshold = 1.26  # threshhold factor above noise sigma

        self.data_file = "fe55.txt"
        self.report_file = "fe55"
        self.report_include_plots = 0  # include plots in report file
        self.make_plots = ["events", "histogram", "cte"]  # list of plots to generate

        self.plot_files = {}  # files to be copied {name:filename}
        self.plot_titles = {}  # plots and title in report {name:title}
        self.show_events = 0  # plot event locations
        self.plot_order = []  # order of plots in report

        self.overscan_correct = 1
        self.zero_correct = 0
        self.combine_images = 0  # True to sum Fe55 images into one image
        self.pause_each_channel = 0  # True to pause after analysis of each channel

        self.system_gain = []
        self.means = []
        self.sdev = []
        self.temperatures = []
        self.mean_fwhm = []  # mean FWHM for each channel
        self.mean_sigma = []  # mean sigma for each channel

        self.hcte_limit = 0.999990
        self.vcte_limit = 0.999990
        self.spec_by_cte = 0
        self.hcte = []
        self.vcte = []

        self.shape = []  # shape parameters

        # [yevents, xevents, zevents, fwhms, sigmas, fwhm_a, fwhm_b, angles] for each channel
        self.event_data = []

        return

    def acquire(self):
        """
        Acquire x-ray images for a CTE, gain, and noise measurements.
        NumberImages is the number of images to take.
        ExposureTime is the exposure time of x-ray image in seconds.
        """

        azcam.log("Acquiring Fe-55 sequence")

        # save pars to be changed
        impars = {}
        azcam.utils.save_imagepars(impars)

        # create new subfolder
        currentfolder, newfolder = azcam.utils.make_file_folder("fe55")
        azcam.db.parameters.set_par("imagefolder", newfolder)

        # clear device
        azcam.db.tools["exposure"].test(0)

        azcam.db.parameters.set_par("imageroot", "fe55.")  # for automatic data analysis
        azcam.db.parameters.set_par(
            "imageincludesequencenumber", 1
        )  # use sequence numbers
        azcam.db.parameters.set_par("imageautoname", 0)  # manually set name
        azcam.db.parameters.set_par(
            "imageautoincrementsequencenumber", 1
        )  # inc sequence numbers
        azcam.db.parameters.set_par("imagetest", 0)  # turn off TestImage

        # loop through images
        for imgnum in range(self.number_images_acquire):

            azcam.log(
                "Image set %d of %d for %.3f seconds..."
                % (imgnum + 1, self.number_images_acquire, self.exposure_time)
            )

            # take bias image
            azcam.db.parameters.set_par("imagetype", "zero")
            azcam.log("Taking bias image")
            azcam.db.tools["exposure"].expose(0, "zero", "bias image")

            # take x-ray image
            azcam.db.parameters.set_par("imagetype", "fe55")
            azcam.log("Taking Fe-55 image")
            azcam.db.tools["exposure"].expose(self.exposure_time, "fe55", "Fe55 image")

        if self.acquire_darks:
            azcam.db.parameters.set_par("imagetype", "dark")
            azcam.log("Taking dark image")
            azcam.db.tools["exposure"].expose(self.exposure_time, "dark", "dark image")

        # finish
        azcam.utils.restore_imagepars(impars, currentfolder)
        azcam.log("Fe-55 finished")

        return

    def analyze(self, filename=""):
        """
        Analyze an exisiting Fe55 image sequence or a single image.
        """

        azcam.log("Analyzing fe55 sequence")

        rootname = "fe55."
        subfolder = "analysis"

        # these arrays are for every chan, maybe for multiple images
        self.event_data = []
        self.system_gain = []
        self.mean_fwhm = []  # array for each channel
        self.mean_sigma = []  # array for each channel
        middle = (self.neighborhood_size - 1) / 2  # size should be odd
        middle = int(middle)

        startingfolder = azcam.utils.curdir()

        if self.overscan_correct or self.zero_correct:
            # create analysis subfolder
            startingfolder, subfolder = azcam.utils.make_file_folder(subfolder)

            # copy all image files to analysis folder
            azcam.log("Making copy of image files for analysis")
            for filename in glob.glob(os.path.join(startingfolder, "*.fits")):
                shutil.copy(filename, subfolder)

            azcam.utils.curdir(subfolder)  # move for analysis folder - assume it already exists
        else:
            pass

        currentfolder = azcam.utils.curdir()
        _, StartingSequence = azcam.utils.find_file_in_sequence(rootname)
        SequenceNumber = StartingSequence

        # get noise roi
        nroi = azcam.utils.get_image_roi()[1]
        self.noise_dn = []
        self.read_noise = []

        # first image is a zero, use it for noise
        zerofilename = rootname + "%04d" % StartingSequence
        zerofilename = azcam.utils.make_image_filename(zerofilename)
        NumExt, first_ext, last_ext = azcam.fits.get_extensions(zerofilename)
        self.num_chans = last_ext - first_ext

        # get overscan noise from zero
        zeroim = pyfits.open(zerofilename)
        for chan, ext in enumerate(range(first_ext, last_ext)):
            hdr = zeroim[ext].header
            ncols = hdr["NAXIS1"]
            nrows = hdr["NAXIS2"]
            imbuf = numpy.reshape(zeroim[ext].data, [nrows, ncols])  # [rows,cols]
            noise = imbuf[nroi[2] : nroi[3], nroi[0] : nroi[1]].std()
            self.noise_dn.append(noise)
        zeroim.close()

        SequenceNumber += 1

        # Correct fe55 image
        if self.overscan_correct or self.zero_correct:
            filename = os.path.join(currentfolder, rootname + "%04d" % SequenceNumber) + ".fits"
            NumExt, first_ext, last_ext = azcam.fits.get_extensions(filename)

            # zero_correct image first
            if self.zero_correct:
                debiased = azcam.db.tools["bias"].debiased_filename
                azcam.log("zero_correct image: %s" % os.path.basename(filename))
                zerosub = "zerosub.fits"
                azcam.fits.sub(filename, debiased, zerosub)
                os.remove(filename)
                os.rename(zerosub, filename)

            # overscan_correct image second
            if self.overscan_correct:
                azcam.log("overscan_correct image: %s" % os.path.basename(filename))
                azcam.fits.colbias(filename, fit_order=self.fit_order)
        else:
            filename = os.path.join(currentfolder, rootname + "%04d" % SequenceNumber) + ".fits"

        self.grade = "UNKNOWN"
        azcam.log("Analyzing image %s" % os.path.basename(filename))

        # get image info
        NumExt, first_ext, last_ext = azcam.fits.get_extensions(filename)

        # get this image section size
        if NumExt > 1:
            ext = 1
        else:
            ext = 0
        reply = azcam.fits.get_section(filename, "DATASEC", ext)
        xedges = []
        yedges = []
        for i in range(middle + 1):
            xedges.append(i)
            xedges.append(reply[1] + i)
            yedges.append(i)
            yedges.append(reply[3] + i)

        # get image data
        fe55im = pyfits.open(filename)
        hdr = fe55im[ext].header
        ncols = hdr["NAXIS1"]
        nrows = hdr["NAXIS2"]
        first_col = 1
        first_row = 1
        last_col = ncols
        last_row = nrows

        # setup
        self.number_events = []
        oldpause = self.pause_each_channel

        azcam.log("neighborhood_size is %d pixels" % self.neighborhood_size)
        azcam.log("Threshold is %.0f DN" % self.threshold)

        # data buffers for plots
        self.imbufs = []
        self.hist_x = []
        self.hist_y = []
        self.xevents = []
        self.yevents = []
        self.z = []
        self.hcte = []
        self.vcte = []
        self.fit_yhcte = []
        self.fit_yvcte = []

        # new gain estimate
        if self.gain_estimate == []:
            self.gain_estimate = azcam.db.tools["gain"].system_gain
            if self.gain_estimate == []:
                self.gain_estimate = NumExt * [1.0]

        if self.threshold == 0:
            if azcam.db.tools["bias"].valid:
                self.threshold = [self.noise_threshold * sd for sd in azcam.db.tools["bias"].sdev]

        # process each channel
        self.chansanalyzed = 0
        for chan, ext in enumerate(range(first_ext, last_ext)):

            # check if analyzing only one ext
            if self.ext_analyze != -1:
                if self.ext_analyze != chan:
                    self.event_data.append([0, 0, 0, 0, 0, 0, 0, 0])
                    continue

            # get data for each channel
            azcam.log("\nAnalyzing channel %d " % chan)

            # get data as [rows,cols]
            imbuf = numpy.reshape(fe55im[ext].data, [nrows, ncols])
            self.imbufs.append(imbuf)

            # new code for clusters
            data_max = scipy.ndimage.filters.maximum_filter(imbuf, self.neighborhood_size)
            maxima = imbuf == data_max
            data_min = scipy.ndimage.filters.minimum_filter(imbuf, self.neighborhood_size)
            diff = (data_max - data_min) > self.threshold
            maxima[diff == 0] = 0

            labeled, num_objects = scipy.ndimage.label(maxima)  # point 0 or 1
            slices = scipy.ndimage.find_objects(labeled)  # vertices containing objects

            # show events
            if self.show_events:
                azcam.plot.plt.figure()
                azcam.plot.plt.imshow(labeled, cmap="gray")

            # these arrays are for each channel
            xevents, yevents, zevents, fwhms, sigmas, gaussians = [], [], [], [], [], []
            xevents1, yevents1, zevents1 = [], [], []
            fwhm_a, fwhm_b, angles = [], [], []

            # analyze neighborhoods
            for dy, dx in slices:
                if 1:
                    x_center = (dx.start + dx.stop - 1) / 2
                    y_center = (dy.start + dy.stop - 1) / 2
                else:
                    x_center = dx
                    y_center = dy

                if x_center in xedges:
                    continue
                if y_center in yedges:
                    continue

                # get sum of neighborhood
                z = 0
                for i in range(-middle + 1, middle):
                    row = y_center + i
                    row = int(row)
                    if row >= nrows:
                        continue
                    for j in range(-middle + 1, middle):
                        col = x_center + j
                        col = int(col)
                        if col >= ncols:
                            continue
                        z += imbuf[row][col]

                xevents1.append(x_center)
                yevents1.append(y_center)
                zevents1.append(z)

            # get rid of outliers
            nevents = len(xevents1)
            s = "Number of raw events found = %d" % (nevents)
            azcam.log(s)

            m1 = (self.xray_lines["K-alpha"] / self.gain_estimate[chan]) * 0.80
            m2 = (self.xray_lines["K-alpha"] / self.gain_estimate[chan]) * 1.2

            # save coords
            for i in range(nevents):
                if (zevents1[i] >= m1) and (zevents1[i] <= m2):
                    xevents.append(xevents1[i])
                    yevents.append(yevents1[i])
                    zevents.append(zevents1[i])
                else:
                    pass  # exclude
            self.yevents.append(yevents)
            self.xevents.append(xevents)

            # trouble can happen here...
            if len(zevents) == 0:
                azcam.log("No events in channel %d" % chan)
                self.event_data.append([0, 0, 0, 0, 0, 0, 0, 0])
                self.hist_x.append(numpy.array(0))
                self.hist_y.append(numpy.array(0))
                self.system_gain.append(self.gain_estimate[chan])
                continue

            azcam.log("Removed %d of %d values" % (nevents - len(xevents), nevents))
            nevents = len(xevents)
            s = "Total number of events = %d" % (nevents)
            azcam.log(s)

            # gaussian fit each event for PSF analysis
            if self.fit_psf:
                if self.max_events != -1:  # limit events per chan
                    nevents = min(nevents, self.max_events)
                self.number_events.append(nevents)
                azcam.log("Fitting gaussians for %d events" % nevents)
                with warnings.catch_warnings():  # surpress warning
                    warnings.simplefilter("ignore")
                    for i in range(nevents):
                        # if i%100==0:
                        #    azcam.log('Events remaining: %05d\r' % (nevents-i)),
                        r1 = yevents[i] - middle
                        r2 = r1 + self.neighborhood_size
                        r1 = int(r1)
                        r2 = int(r2)
                        c1 = xevents[i] - middle
                        c2 = c1 + self.neighborhood_size
                        c1 = int(c1)
                        c2 = int(c2)

                        reply = self._fit_gauss_elliptical(
                            [xevents[i], yevents[i]], imbuf[r1:r2, c1:c2]
                        )  # was box
                        fwhm = self.pixel_size * math.sqrt(0.5 * (reply[5] ** 2 + reply[6] ** 2))

                        sigma = fwhm / CON1
                        sigmas.append(sigma)
                        fwhms.append(fwhm)
                        gaussians.append(reply)

                # make numpy arrays
                fwhm_a = [x[5] for x in gaussians]
                fwhm_b = [x[6] for x in gaussians]
                angles = [x[7] for x in gaussians]

                fm = numpy.array(fwhms).mean()  # mean for this channel
                sm = numpy.array(sigmas).mean()

                # from Jim Chiang for LSST
                fm = math.sqrt(fm ** 2 - ((1.0 / 6.0) * self.pixel_size) ** 2)
                sm = math.sqrt(sm ** 2 - ((1.0 / 6.0) * self.pixel_size) ** 2)

                self.mean_fwhm = self.mean_fwhm.append(fm)
                self.mean_sigma = self.mean_sigma.append(sm)

                s = "FWHM_%d = %5.3f (sigma = %.2f um)" % (chan, fm, sm)
                azcam.log(s)

            else:
                sigmas = []
                fwhms = []
                fwhm_a = []
                fwhm_b = []
                gaussians = []
                angles = []
                fm = 0.0
                sm = 0.0
                self.mean_fwhm = []
                self.mean_sigma = []

            # make single data array
            self.event_data.append(
                [yevents, xevents, zevents, fwhms, sigmas, fwhm_a, fwhm_b, angles]
            )

            # calculate and save shape info
            if self.fit_psf:
                shape1 = (
                    self.event_data[chan][5].mean() / self.event_data[chan][6].mean()
                )  # fwhm_a / fwhm_b
                shape2 = numpy.array(self.event_data[chan][7]).mean()
                self.shape.append([shape1, shape2])
                azcam.log("Shape: %5.03f, %7.03f" % (shape1, shape2))

            # make new image with only summed events
            events = numpy.zeros([nrows, ncols])
            for i in range(len(xevents)):
                events[int(yevents[i])][int(xevents[i])] = zevents[i]
            self.Events = events

            # calc histogram
            bmin = int(numpy.array(zevents).min() - 100)
            bmax = int(numpy.array(zevents).max() + 100)
            numbins = int((bmax - bmin + 1) / self.bin_size)  # sum bins for nice plot
            N, bins = numpy.histogram(zevents, numbins, range=(bmin, bmax))  # -1 new
            self.N = N
            self.Bins = bins

            # get gain from histogram max
            bin_max = numpy.where(N == N.max())
            maxvalue = bins[bin_max][0]
            g = self.xray_lines["K-alpha"] / maxvalue
            self.system_gain.append(g)
            s = "Gain_%d = %.2f" % (chan, g)
            azcam.log(s)

            # correct readnoise
            noise = self.noise_dn[chan]
            if self.system_noise_correction == []:
                self.read_noise.append(noise * g)
            else:
                rn = g * math.sqrt(noise ** 2 - self.system_noise_correction[chan] ** 2)
                self.read_noise.append(rn)

            # save for histogram plot
            self.hist_x.append(bins[1:])
            self.hist_y.append(N)

            # HCTE plot with line fit
            z = []
            for i, c in enumerate(self.event_data[chan][1]):  # loop over column number
                r = self.event_data[chan][0][i]  # row number
                r = int(r)
                c = int(c)
                z.append(events[r][c])
            self.z.append(numpy.array(z))
            coefs = numpy.lib.polyfit(self.event_data[chan][1], z, 1)
            fit_y = numpy.lib.polyval(coefs, list(range(first_col, last_col + 1)))
            self.fit_yhcte.append(fit_y)

            hslope = coefs[0]
            hcte = 1.0 + g * (hslope / self.xray_lines["K-alpha"])
            hcte = min(1.0, hcte)
            self.hcte.append(hcte)
            s = "HCTE_%d = %0.6f" % (chan, hcte)
            azcam.log(s)

            # VCTE line fit
            z = []
            for i, r in enumerate(self.event_data[chan][0]):  # loop over row number
                c = self.event_data[chan][1][i]  # col number
                r = int(r)
                c = int(c)
                z.append(events[r][c])
            coefs = numpy.lib.polyfit(self.event_data[chan][0], z, 1)
            fit_y = numpy.lib.polyval(coefs, list(range(first_row, last_row + 1)))
            self.fit_yvcte.append(fit_y)

            vslope = coefs[0]
            vcte = 1.0 + g * (vslope / self.xray_lines["K-alpha"])
            vcte = min(1.0, vcte)
            self.vcte.append(vcte)
            s = "VCTE_%d = %0.6f" % (chan, vcte)
            azcam.log(s)

            self.chansanalyzed += 1
            if self.pause_each_channel and NumExt > 1:
                reply = azcam.utils.prompt(
                    "Press Enter to continue to next channel [c to continue w/o pause, s to stop]"
                )
                if reply.lower() == "c":
                    oldpause = self.pause_each_channel
                    self.pause_each_channel = 0
                elif reply.lower() == "s":
                    break

            if self.spec_by_cte:
                if self.grade == "FAIL":  # already failed on a previous amp
                    pass
                else:
                    if vcte >= self.vcte_limit and hcte >= self.hcte_limit:
                        self.grade = "PASS"
                    else:
                        self.grade = "FAIL"

        self.pause_each_channel = oldpause

        if self.fit_psf:
            fm = numpy.array(self.mean_fwhm).mean()
            sm = numpy.array(self.mean_sigma).mean()
            s = "Mean FWHM for all channels: %5.2f (sigma = %.2f um)" % (fm, sm)
            azcam.log(s)

        if not self.spec_by_cte and (self.spec_sigma != -1 and self.fit_psf):
            if sm <= self.spec_sigma:
                self.grade = "PASS"
            else:
                self.grade = "FAIL"

        s = "Grade = %s" % self.grade
        azcam.log(s)

        if not self.grade_sensor:
            self.grade = "UNDEFINED"

        # read noise grade
        if self.readnoise_spec != -1:
            if numpy.array(self.read_noise).max() > self.readnoise_spec:
                self.grade_read_noise = "FAIL"
            else:
                self.grade_read_noise = "PASS"
        if not self.grade_sensor:
            self.grade_read_noise = "UNDEFINED"

        # close image file
        fe55im.close()

        # stats over multiple images
        if self.fit_psf:
            self.mean_fwhmTotal = numpy.array(self.mean_fwhm).mean()
            self.mean_sigmaTotal = numpy.array(self.mean_sigma).mean()

        # make plots
        self.plot()

        # copy analysis output to starting fold
        if startingfolder != subfolder:
            try:
                shutil.copy("fe55.fits", startingfolder)  # filename perhaps, but overwrites
            except Exception:
                pass
            for f in list(self.plot_files.values()):
                try:
                    shutil.copy(f, startingfolder)
                except Exception:
                    pass

        # define dataset
        self.dataset = {
            "data_file": self.data_file,
            "grade": self.grade,
            "chansanalyzed": self.chansanalyzed,
            "neighborhood_size": self.neighborhood_size,
            "threshhold": self.threshold,
            "system_gain": self.system_gain,
            "noise_dn": self.noise_dn,
            "grade_read_noise": self.grade_read_noise,
            "read_noise": self.read_noise,
            "mean_fwhmTotal": self.mean_fwhmTotal,
            "mean_sigmaTotal": self.mean_sigmaTotal,
            "self.shape": self.shape,
            "system_noise_correction": self.system_noise_correction,
            "number_events": self.number_events,
            "mean_fwhm": self.mean_fwhm,
            "mean_sigma": self.mean_sigma,
            # 'event_data': self.event_data,
        }

        # write output files
        azcam.utils.curdir(startingfolder)
        self.write_datafile()
        if self.create_reports:
            self.report()

        del self.imbufs  # new, may help file lock 07sep16

        self.valid = True

        return

    def plot(self):
        """
        Make plots.
        """

        # set plot parameters (get with figure(1).subplotpars.left, etc.)
        if self.num_chans == 1:
            showlabels = 1
            nrows = 1
            ncols = 1
            ptop = 0.86
            pbottom = 0.17
            pleft = 0.15
            pright = 0.95
            wspace = 0.3
            hspace = 0.92
            large_font = 18
            medium_font = 16
            small_font = 14
        elif self.num_chans == 2:
            showlabels = 1
            nrows = 2
            ncols = 1
            ptop = 0.86
            pbottom = 0.17
            pleft = 0.15
            pright = 0.95
            wspace = 0.3
            hspace = 1.0
            large_font = 18
            medium_font = 16
            small_font = 14
        elif self.num_chans == 4:
            showlabels = 1
            nrows = 2
            ncols = 2
            ptop = 0.845
            pbottom = 0.124
            pleft = 0.080
            pright = 0.959
            wspace = 0.249
            hspace = 0.602
            large_font = 18
            medium_font = 16
            small_font = 14
        elif self.num_chans == 8:
            showlabels = 1
            nrows = 2
            ncols = 4
            ptop = None
            pbottom = None
            pleft = 0.10
            pright = 0.95
            wspace = 0.38
            hspace = 0.45
            large_font = 18
            medium_font = 16
            small_font = 14
        elif self.num_chans == 16:
            showlabels = 0
            nrows = 4
            ncols = 4
            ptop = None
            pbottom = None
            pleft = 0.10
            pright = 0.95
            wspace = 0.45
            hspace = 0.55
            large_font = 14
            medium_font = 12
            small_font = 10
        else:
            nrows = 1
            ncols = 1
            showlabels = 1
            pleft = None
            pright = None
            pbottom = None
            ptop = None
            wspace = None
            hspace = None
            large_font = 18
            medium_font = 16
            small_font = 14

        # plot raw events
        if "events" in self.make_plots:
            fig_events = azcam.plot.plt.figure()
            fignum = fig_events.number
            azcam.plot.move_window(fignum)
            fig_events.suptitle(r"$\rm{X-Ray\ Events}$", fontsize=large_font)
            fig_events.tight_layout()
            fig_events.subplots_adjust(
                left=pleft,
                bottom=pbottom,
                right=pright,
                top=ptop,
                wspace=wspace,
                hspace=hspace,
            )

            chan = 0
            plotnum = 1
            for _ in range(nrows):
                for _ in range(ncols):
                    azcam.plot.plt.subplot(nrows, ncols, plotnum)
                    if self.num_chans == 1:
                        s1 = ""
                    else:
                        s1 = "Chan " + str(chan + 1)
                    azcam.plot.plt.title(s1, fontsize=medium_font)
                    ax = azcam.plot.plt.gca()

                    median = numpy.median(self.imbufs[chan])
                    if median < 0:
                        m1 = 0
                        m2 = 100
                    else:
                        m1 = int(median / 5.0)
                        m2 = int(median * 5.0)

                    if 1:
                        azcam.plot.plt.imshow(
                            self.imbufs[chan],
                            cmap="gray",
                            interpolation="none",
                            vmin=m1,
                            vmax=m2,
                        )
                        nc = len(self.imbufs[chan][0])
                        nr = len(self.imbufs[chan])
                        azcam.plot.plt.xlim(1, nc)
                        azcam.plot.plt.ylim(1, nr)
                        _, labels = azcam.plot.plt.xticks()
                        azcam.plot.plt.setp(labels, rotation=45)

                    if 1:
                        # mark valid events on events plot
                        azcam.plot.plt.autoscale(False)
                        azcam.plot.plt.scatter(
                            self.xevents[chan],
                            self.yevents[chan],
                            s=10,
                            facecolors="none",
                            edgecolors="r",
                        )

                    if showlabels:
                        ax.set_xlabel("Cols")
                        ax.set_ylabel("Rows")
                    else:
                        ax.xaxis.set_ticks([])
                        ax.yaxis.set_ticks([])

                    azcam.plot.update()

                    chan += 1
                    plotnum += 1

            self.plot_files["events"] = "events.png"
            self.plot_titles["events"] = "X-Ray Events"
            azcam.plot.save_figure(fignum, f"{self.plot_files['events']}")

        if "histogram" in self.make_plots:
            fig_hist = azcam.plot.plt.figure()
            fignum = fig_hist.number
            azcam.plot.move_window(fignum)
            fig_hist.suptitle(r"$\rm{X-Ray\ Histograms}$", fontsize=large_font)
            fig_hist.subplots_adjust(
                left=0.125,
                bottom=0.175,
                right=0.977,
                top=0.824,
                wspace=0.343,
                hspace=1.0,
            )

            chan = 0
            plotnum = 1
            for _ in range(nrows):
                for _ in range(ncols):
                    azcam.plot.plt.subplot(nrows, ncols, plotnum)
                    if self.num_chans == 1:
                        s1 = ""
                    else:
                        s1 = "Chan " + str(chan)
                    azcam.plot.plt.title(s1, fontsize=medium_font)
                    ax = azcam.plot.plt.gca()
                    azcam.plot.plt.plot(self.hist_x[chan], self.hist_y[chan], "b-")
                    ax.set_yscale("linear")
                    for label in ax.xaxis.get_ticklabels():
                        label.set_rotation(45)
                        label.set_fontsize(small_font)
                    if showlabels:
                        ax.set_xlabel("Value")
                        ax.set_ylabel("Num. Events")
                    ax.grid(True)
                    _, labels = azcam.plot.plt.xticks()
                    azcam.plot.plt.setp(labels, rotation=45)

                    # azcam.plot.plt.xlim(zmedian/2.,zmedian*2.)
                    # azcam.plot.plt.xlim(self.z[chan].min()-100, self.z[chan].max() + 200)

                    hist_max = self.xray_lines["K-alpha"] / self.system_gain[chan]
                    azcam.plot.plt.axvline(x=hist_max, linewidth=1, color="k", linestyle="--")

                    chan += 1
                    plotnum += 1

            self.plot_files["histogram"] = "histogram.png"
            self.plot_titles["histogram"] = "Histograms"
            azcam.plot.save_figure(fignum, "%s" % self.plot_files["histogram"])

        if "cte" in self.make_plots:
            last_col = len(self.imbufs[0][0])
            last_row = len(self.imbufs[0])

            # HCTE
            fig_cte = azcam.plot.plt.figure()
            fignum = fig_cte.number
            azcam.plot.move_window(fignum)
            fig_cte.suptitle(r"$\rm{HCTE}$", fontsize=large_font)
            fig_cte.subplots_adjust(
                left=pleft,
                bottom=pbottom,
                right=pright,
                top=ptop,
                wspace=wspace,
                hspace=hspace,
            )
            # fig_cte.subplots_adjust(hspace=0.40, wspace=0.30)

            chan = 0
            plotnum = 1
            for _ in range(nrows):
                for _ in range(ncols):
                    azcam.plot.plt.subplot(nrows, ncols, plotnum)
                    if self.num_chans == 1:
                        s1 = ""
                    else:
                        s1 = "Chan " + str(chan + 1)
                    azcam.plot.plt.title(s1, fontsize=medium_font)
                    ax = azcam.plot.plt.gca()

                    azcam.plot.plt.title("Chan %d" % chan)

                    azcam.plot.plt.plot(self.event_data[chan][1], self.z[chan], "ro", markersize=2)
                    azcam.plot.plt.plot(list(range(1, last_col + 1)), self.fit_yhcte[chan], "b-")
                    azcam.plot.plt.ylim(self.z[chan].min() - 100, self.z[chan].max() + 200)
                    azcam.plot.plt.xlim(1, last_col)

                    s = "%0.6f" % (self.hcte[chan])
                    azcam.plot.plt.annotate(
                        s,
                        xy=(0.15, 0.85),
                        xycoords="axes fraction",
                        bbox=dict(boxstyle="round,pad=0.1", fc="yellow", alpha=1.0),
                    )

                    # ax.xaxis.set_ticks([])
                    # ax.yaxis.set_ticks([])
                    _, labels = azcam.plot.plt.xticks()
                    azcam.plot.plt.setp(labels, rotation=45)

                    azcam.plot.update()
                    chan += 1
                    plotnum += 1

            self.plot_files["hcte"] = "hcte.png"
            self.plot_titles["hcte"] = "HCTE"
            azcam.plot.save_figure(fignum, "%s" % self.plot_files["hcte"])

            # VCTE
            fig_cte = azcam.plot.plt.figure()
            fignum = fig_cte.number
            azcam.plot.move_window(fignum)
            fig_cte.suptitle(r"$\rm{VCTE}$", fontsize=large_font)
            fig_cte.subplots_adjust(
                left=pleft,
                bottom=pbottom,
                right=pright,
                top=ptop,
                wspace=wspace,
                hspace=hspace,
            )
            # fig_cte.subplots_adjust(hspace=0.40, wspace=0.30)
            chan = 0
            plotnum = 1
            for _ in range(nrows):
                for _ in range(ncols):
                    azcam.plot.plt.subplot(nrows, ncols, plotnum)
                    if self.num_chans == 1:
                        s1 = ""
                    else:
                        s1 = "Chan " + str(chan + 1)
                    azcam.plot.plt.title(s1, fontsize=medium_font)
                    ax = azcam.plot.plt.gca()

                    azcam.plot.plt.title("Chan %d" % chan)

                    azcam.plot.plt.plot(self.event_data[chan][0], self.z[chan], "ro", markersize=2)
                    azcam.plot.plt.plot(list(range(1, last_row + 1)), self.fit_yvcte[chan], "b-")
                    azcam.plot.plt.ylim(self.z[chan].min() - 100, self.z[chan].max() + 200)
                    azcam.plot.plt.xlim(1, last_row)

                    s = "%0.6f" % (self.vcte[chan])
                    azcam.plot.plt.annotate(
                        s,
                        xy=(0.15, 0.85),
                        xycoords="axes fraction",
                        bbox=dict(boxstyle="round,pad=0.1", fc="yellow", alpha=1.0),
                    )

                    # ax.xaxis.set_ticks([])
                    # ax.yaxis.set_ticks([])
                    _, labels = azcam.plot.plt.xticks()
                    azcam.plot.plt.setp(labels, rotation=45)

                    azcam.plot.update()
                    chan += 1
                    plotnum += 1

            self.plot_files["vcte"] = "vcte.png"
            self.plot_titles["vcte"] = "VCTE"
            azcam.plot.save_figure(fignum, "%s" % self.plot_files["vcte"])

        azcam.plot.plt.show()

        return

    def report(self):
        """
        Write dark report file.
        """

        lines = ["# X-Ray Analysis", ""]

        if self.grade != "UNDEFINED":
            s = "X-Ray grade = %s" % self.grade
            lines.append(s)
            lines.append("")

        if self.spec_sigma != -1:
            s = "neighborhood_size = %d pixels" % self.neighborhood_size
            lines.append(s)
            lines.append("")
            s = "Threshhold = %.0f DN" % self.threshold
            lines.append(s)
            lines.append("")
            s = "TotalEvents = %.0f" % sum(self.number_events)
            lines.append(s)
            lines.append("")

        # means for entire device
        if self.fit_psf:
            s = "Mean FWHM = %5.01f microns" % self.mean_fwhmTotal
            lines.append(s)
            lines.append("")
            s = "Mean Sigma = %5.01f microns" % self.mean_sigmaTotal
            lines.append(s)
            lines.append("")

        # Gain and Noise
        if self.system_noise_correction == []:
            s = "Read Noise in electrons IS NOT system noise corrected"
        else:
            s = "Read Noise in electrons IS system noise corrected"
            lines.append(s)
            lines.append("")
            s = (
                "Mean system_noise_correction = %5.01f DN"
                % numpy.array(self.system_noise_correction).mean()
            )
        lines.append(s)
        lines.append("")

        s = "|**Channel**|**Gain [e/DN]**|**Noise [DN]**|**Noise [e]**|"
        lines.append(s)
        s = "|:---|:---:|:---:|:---:|"
        lines.append(s)
        for chan in range(len(self.read_noise)):
            s = f"|{chan:02d}|{self.system_gain[chan]:5.02f}|{self.noise_dn[chan]:5.01f}|{self.read_noise[chan]:5.1f}|"
            lines.append(s)
        lines.append("")

        # add plots
        if self.report_include_plots:
            if self.plot_order == []:
                names = list(self.plot_files.keys())
                names.sort()
            else:
                names = self.plot_order
            for name in names:
                lines.append(
                    f"![{self.plot_titles[name]}]({os.path.abspath(self.plot_files[name])})  "
                )
                lines.append("")
                lines.append(f"{self.plot_titles[name]}.")
                lines.append("")

        # Make report files
        self.write_report(self.report_file, lines)

        return

    def _fit_gauss_elliptical(self, xy, data):
        """
        Purpose

        Fitting a star with a 2D elliptical gaussian PSF.

        Inputs
        * xy (list) = list with the form [x,y] where x and y are the integer positions in the complete image of
        the first pixel (the one with x=0 and y=0) of the small subimage that is used for fitting.
        * data (2D Numpy array) = small subimage, obtained from the full FITS image by slicing. It must contain
        a single object : the star to be fitted, placed approximately at the center.

        Output (list) = list with 8 elements, in the form:
        [maxi, floor, height, mean_x, mean_y, fwhm_small, fwhm_large, angle].
        The list elements are respectively:
        - maxi is the value of the star maximum signal,
        - floor is the level of the sky background (fit result),
        - height is the PSF amplitude (fit result),
        - mean_x and mean_y are the star centroid x and y positions, on the full image (fit results),
        - fwhm_small is the smallest full width half maximum of the elliptical gaussian PSF (fit result) in pixels
        - fwhm_large is the largest full width half maximum of the elliptical gaussian PSF (fit result) in pixels
        - angle is the angular direction of the largest fwhm, measured clockwise starting from the vertical direction
          (fit result) and expressed in degrees. The direction of the smallest fwhm is obtained by adding 90 deg to angle.
        """

        # find starting values
        dat = data.flatten()
        maxi = data.max()
        floor = numpy.ma.median(dat)
        height = maxi - floor
        if (
            height == 0.0
        ):  # if star is saturated it could be that median value is 32767 or 65535 --> height=0
            floor = numpy.mean(dat)
            height = maxi - floor

        mean_x = (numpy.shape(data)[0] - 1) / 2
        mean_y = (numpy.shape(data)[1] - 1) / 2

        fwhm = numpy.sqrt(numpy.sum((data > floor + height / 2.0).flatten()))
        fwhm_1 = fwhm
        fwhm_2 = fwhm
        sig_1 = fwhm_1 / CON1
        sig_2 = fwhm_2 / CON1

        angle = 0.0

        p0 = floor, height, mean_x, mean_y, sig_1, sig_2, angle

        # ---------------------------------------------------------------------------------
        # fitting gaussian
        def gauss(floor, height, mean_x, mean_y, sig_1, sig_2, angle):

            A = (numpy.cos(angle) / sig_1) ** 2.0 + (numpy.sin(angle) / sig_2) ** 2.0
            B = (numpy.sin(angle) / sig_1) ** 2.0 + (numpy.cos(angle) / sig_2) ** 2.0
            C = (
                2.0
                * numpy.sin(angle)
                * numpy.cos(angle)
                * (1.0 / (sig_1 ** 2.0) - 1.0 / (sig_2 ** 2.0))
            )

            # do not forget factor 0.5 in exp(-0.5*r**2./sig**2.)
            return lambda x, y: floor + height * numpy.exp(
                -0.5
                * (
                    A * ((x - mean_x) ** 2)
                    + B * ((y - mean_y) ** 2)
                    + C * (x - mean_x) * (y - mean_y)
                )
            )

        def err(p, data):
            return numpy.ravel(gauss(*p)(*numpy.indices(data.shape)) - data)

        p = scipy.optimize.leastsq(err, p0, args=(data), maxfev=200)
        p = p[0]

        # ---------------------------------------------------------------------------------
        # formatting results
        floor = p[0]
        height = p[1]
        mean_x = p[2] + xy[0]
        mean_y = p[3] + xy[1]

        # angle gives the direction of the p[4]=sig_1 axis, starting from x (vertical) axis, clockwise in direction of y (horizontal) axis
        if numpy.abs(p[4]) > numpy.abs(p[5]):

            fwhm_large = numpy.abs(p[4]) * CON1
            fwhm_small = numpy.abs(p[5]) * CON1
            angle = numpy.arctan(numpy.tan(p[6]))

        else:  # then sig_1 is the smallest : we want angle to point to sig_y, the largest

            fwhm_large = numpy.abs(p[5]) * CON1
            fwhm_small = numpy.abs(p[4]) * CON1
            angle = numpy.arctan(numpy.tan(p[6] + numpy.pi / 2.0))

        output = [maxi, floor, height, mean_x, mean_y, fwhm_small, fwhm_large, angle]

        return output
