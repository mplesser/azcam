"""
Observe class for GUI use.

Notes:
IPython config needs:
 c.InteractiveShellApp.gui = 'qt'
 c.InteractiveShellApp.pylab = 'qt'
"""

import os
import sys
import time

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QTimer, Signal, Slot
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QTableWidgetItem
from PySide6.QtCore import QCoreApplication

import azcam
from azcam.tools import Tools
from azcam.observe.observe_common import ObserveCommon
from azcam.observe.observe_qt.observe_gui_ui import Ui_observe


class GenericWorker(QtCore.QObject):
    start = Signal(str)

    finished = Signal()

    def __init__(self, function, *args, **kwargs):
        super(GenericWorker, self).__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.start.connect(self.run)

    @Slot()
    def run(self, *args, **kwargs):
        self.function(*self.args, **self.kwargs)
        self.finished.emit()


class ObserveQt(ObserveCommon, Tools, QMainWindow):
    """
    The Observe class which implements observing scripts.

    This class is instantiated as the *observe* tool.
    Scripts may be run from a text file using .observe() or executed within
    loaded a GUI using .start().
    """

    def __init__(self, tool_id="observe"):
        ObserveCommon.__init__(self)
        Tools.__init__(self, tool_id)
        QMainWindow.__init__(self)

        self.et_scale = 1.0  # exposure time scale factor

        self.threadPool = []

        # timer/tickers
        self._index = 0
        self.tickers = ["|", "/", "-", "\\"]

        # focus component for motion - instrument or telescope
        self.focus_component = "instrument"

    def initialize_qt(self):
        """
        Initialize observe.
        """

        self.gui_mode = 1

        # QWidget.__init__(self, parent)
        self.parent = None

        # QMainWindow()
        self.ui = Ui_observe()
        self.ui.setupUi(self)

        # connect buttons
        self.ui.pushButton_abort_script.released.connect(self.abort_script)
        self.ui.pushButton_run.released.connect(self.run_thread)
        self.ui.pushButton_selectscript.released.connect(self.select_script)
        self.ui.pushButton_editscript.released.connect(self.edit_script)
        self.ui.pushButton_loadscript.released.connect(self.load_script)
        self.ui.pushButton_pause_script.released.connect(self.pause_script)
        self.ui.pushButton_scale_et.released.connect(self.scale_exptime)

        # connect check box
        self.ui.checkBox_azalt.stateChanged.connect(self.set_azalt)

        # self.ui.tableWidget_script.resizeColumnsToContents()
        self.ui.tableWidget_script.setAlternatingRowColors(True)

        # event when table cells change
        self.ui.tableWidget_script.itemChanged.connect(self.cell_changed)

        # create and start a timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._watchdog)
        self.timer.start(500)

        # get parameters from parfile
        try:
            self.script_file = azcam.db.parameters.get_local_par(
                "observe", "script_file", "default", "", "observing_script.txt"
            )
            self.ui.plainTextEdit_filename.setPlainText(self.script_file)
        except Exception as _:
            pass

        try:
            number_cycles = azcam.db.parameters.get_local_par(
                "observe", "number_cycles", "default", "", 1
            )
        except Exception as _:
            number_cycles = 1
        try:
            self.number_cycles = int(number_cycles)
            self.ui.spinBox_loops.setValue(self.number_cycles)
        except Exception as _:
            pass

        # define column order
        self.column_order = [
            "cmdnumber",
            "status",
            "command",
            "argument",
            "exptime",
            "type",
            "title",
            "numexp",
            "filter",
            "ra",
            "dec",
            "epoch",
            "expose_flag",
            "movetel_flag",
            "steptel_flag",
            "movefilter_flag",
            "movefocus_flag",
        ]

        self.column_number = {}
        for i, x in enumerate(self.column_order):
            self.column_number[i] = x

    def closeEvent(self, event):
        # save pars
        azcam.db.parameters.set_local_par("observe", "script_file", self.script_file)
        azcam.db.parameters.set_local_par(
            "observe", "number_cycles", self.number_cycles
        )
        azcam.db.parameters.write_parfile()

        print("closing")

        return

    def set_azalt(self, flag=1):
        """
        Set table header to Alt AZ if flag is True.
        """

        self.azalt_mode = self.ui.checkBox_azalt.isChecked()

        ___qtablewidgetitem9 = self.ui.tableWidget_script.horizontalHeaderItem(9)
        ___qtablewidgetitem10 = self.ui.tableWidget_script.horizontalHeaderItem(10)
        if self.azalt_mode:
            ___qtablewidgetitem9.setText(
                QCoreApplication.translate("observe", "AZ", None)
            )
            ___qtablewidgetitem10.setText(
                QCoreApplication.translate("observe", "ALT", None)
            )
        else:
            ___qtablewidgetitem9.setText(
                QCoreApplication.translate("observe", "RA", None)
            )
            ___qtablewidgetitem10.setText(
                QCoreApplication.translate("observe", "DEC", None)
            )

        return

    def update_cell(self, command_number, parameter="", value=""):
        """
        Update one parameter of an existing command.

        :param command_number: Number of command to be updated. If -1, return list of possible arguments.
        :param parameter: Paramater name to be updated.
        :param value: New value of parameter.
        :return: None
        """

        if command_number == -1:
            pars = []
            pars.append("line")
            pars.append("cmdnumber")
            pars.append("status")
            pars.append("command")
            pars.append("argument")
            pars.append("exptime")
            pars.append("type")
            pars.append("title")
            pars.append("numexp")
            pars.append("filter")
            pars.append("focus")
            pars.append("ra")
            pars.append("dec")
            pars.append("ra_next")
            pars.append("dec_next")
            pars.append("epoch")
            pars.append("expose_flag")
            pars.append("movetel_flag")
            pars.append("steptel_flag")
            pars.append("movefilter_flag")
            pars.append("movefocus_flag")

            return pars

        self.commands[command_number][parameter.lower()] = value

        self.update_table()

        return

    def update_line(self, line_number, line):
        """
        Add or update a script line.

        :param line_number: Number of line to be updated or -1 to add at the end of the line buffer.
        :param line: New string (line). If line is "", then line_number is deleted.
        :return: None
        """

        if line_number == -1:
            self.lines.append(line)
            return

        if line == "":
            if line_number < len(self.lines) - 1:
                self.lines.pop(line_number)
                return

        self.lines[line_number] = line

        return

    def scale_exptime(self):
        """
        Scale the current exposure times.
        """

        self.status("Working...")

        self.et_scale = float(self.ui.doubleSpinBox_ExpTimeScale.value())

        for cmdnum, cmd in enumerate(self.commands):
            old = float(cmd["exptime"])
            new = old * self.et_scale
            self.update_cell(cmdnum, "exptime", new)

        self.status("")

        return

    def _watchdog(self):
        """
        Update counter field indicating GUI in running and highlight current table row.
        """

        if not self.gui_mode:
            return

        # check abort
        if self._abort_gui:
            self.status("Aborting GUI")
            print("Aborting observe GUI")
            return

        if self._paused:
            self.status("Script PAUSED")

        # ticker
        x = self.tickers[self._index]  # list of ticker chars
        self.ui.label_counter.setText(x)
        self.ui.label_counter.repaint()
        self._index += 1
        if self._index > len(self.tickers) - 1:
            self._index = 0

        # highlights
        if self._do_highlight:
            row = self.current_line  # no race condition
            if row != -1:
                if self._paused:
                    self.highlight_row(row, 2)
                elif self._abort_script:
                    self.highlight_row(row, 3)
                else:
                    self.highlight_row(row, 1)
                # clear previous row
                if row > 0:
                    self.highlight_row(row - 1, 0)
            self._do_highlight = 0

        # save pars
        self.number_cycles = self.ui.spinBox_loops.value()

        return

    def run_thread(self):
        """
        Start the script execution thread so that _abort_script may be used.
        """

        self.gui_mode = 1

        self.status("Running...")
        self.number_cycles = (
            self.ui.spinBox_loops.value()
        )  # set number of cycles to run script

        my_thread = QtCore.QThread()
        my_thread.start()

        # This causes my_worker.run() to eventually execute in my_thread:
        my_worker = GenericWorker(self._run)
        my_worker.moveToThread(my_thread)
        my_worker.start.emit("hello")
        my_worker.finished.connect(self.run_finished)

        self.threadPool.append(my_thread)
        self.my_worker = my_worker

    def run_finished(self):
        """
        Called when the run thread is finished.
        """

        self.current_line = -1
        self.highlight_row(len(self.commands) - 1, 0)
        self.status("Run finished")  # clear status box

        # save pars
        azcam.db.parameters.write_parfile()

        return

    def select_script(self):
        """
        Select a script file using dialog box.
        """

        filename = str(self.ui.plainTextEdit_filename.toPlainText())
        folder = os.path.dirname(filename)
        filename = QFileDialog.getOpenFileName(
            self.parent, "Select script filename", folder, "Scripts (*.txt)"
        )
        self.ui.plainTextEdit_filename.setPlainText(filename[0])
        filename = str(filename[0])
        azcam.db.parameters.set_local_par("observe", "script_file", filename)

        return

    def edit_script(self):
        """
        Edit the select a script file.
        """

        filename = str(self.ui.plainTextEdit_filename.toPlainText())

        os.startfile(filename)  # opens notepad for .txt files

        return

    def load_script(self):
        """
        Read script file and load into table.
        """

        # open observing script text file
        script_file = str(self.ui.plainTextEdit_filename.toPlainText())
        with open(script_file, "r") as ofile:
            if not ofile:
                self.ui.label_status.setText("could not open script")
                return

        self.script_file = script_file
        self.read_file(script_file)
        self.out_file = self.out_file
        self._parse()

        # fill in table
        self.update_table()

        return

    def cell_changed(self, item):
        """
        Called when a table cell is changed.
        """

        row = item.row()
        col = item.column()
        newvalue = item.text()

        colnum = self.column_number[col]

        self.commands[row][colnum] = newvalue

        return

    def update_table(self):
        """
        Update entire GUI table with current values of .commands.
        """

        # fill in table
        self.ui.tableWidget_script.setRowCount(len(self.commands))
        for row, data1 in enumerate(self.commands):
            col = 0
            for key in self.column_order:
                newitem = QTableWidgetItem(str(data1[key]))
                self.ui.tableWidget_script.setItem(row, col, newitem)
                col += 1

        self.ui.tableWidget_script.resizeColumnsToContents()
        self.ui.tableWidget_script.resizeRowsToContents()
        height = min(300, self.ui.tableWidget_script.verticalHeader().length() + 60)
        self.ui.tableWidget_script.setFixedSize(
            self.ui.tableWidget_script.horizontalHeader().length() + 20, height
        )

        return

    def highlight_row(self, row_number, flag):
        """
        Highlight or unhighlight a row of the GUI table during execution.
        Highlighting cannot occur in thread.
        """

        numcols = self.ui.tableWidget_script.columnCount()

        # higlight row being executed
        if flag == 0:
            # uncolor row
            for col in range(numcols):
                item = self.ui.tableWidget_script.item(row_number, col)
                item.setBackground(QtGui.QColor(QtCore.Qt.transparent))
                self.ui.tableWidget_script.repaint()

        elif flag == 1:
            # green
            for col in range(numcols):
                item = self.ui.tableWidget_script.item(row_number, col)
                item.setBackground(QtGui.QColor(0, 255, 0))
                self.ui.tableWidget_script.repaint()

        elif flag == 2:
            # alt color for pause
            for col in range(numcols):
                item = self.ui.tableWidget_script.item(row_number, col)
                item.setBackground(QtGui.QColor(255, 255, 153))
                self.ui.tableWidget_script.repaint()

        elif flag == 3:
            # alt color for abort
            for col in range(numcols):
                item = self.ui.tableWidget_script.item(row_number, col)
                item.setBackground(QtGui.QColor(255, 100, 100))
                self.ui.tableWidget_script.repaint()

        return

    def wait4highlight(self):
        """
        Wait for row to highlight.
        """

        self._do_highlight = 1
        if self._do_highlight:
            while self._do_highlight:
                time.sleep(0.1)

        return

    def status(self, message):
        """
        Display text in status field.
        """

        self.ui.label_status.setText(str(message))
        self.ui.label_status.repaint()

        return

    def abort_script(self):
        """
        Abort a running script as soon as possible.
        """

        self._abort_script = 1
        self.status("Abort detected")

        # self.wait4highlight()
        self._do_highlight = 1

        return

    def pause_script(self):
        """
        Pause a running script as soon as possible.
        """

        self._paused = not self._paused
        if self._paused:
            s = "Pause detected"
        else:
            s = "Running..."
        self.status(s)

        # self.wait4highlight()
        self._do_highlight = 1

        return

    def start(self):
        """
        Show the GUI.
        """

        self.initialize_qt()

        # show GUI
        self.show()
        self.status("ready...")

        # set window location
        self.move(50, 50)

        return

    def stop(self):
        """
        Stop the GUI for the Observe class.
        """

        self._abort_gui = 1

        return
