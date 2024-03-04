# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'observe_gui.ui'
##
## Created by: Qt User Interface Compiler version 6.4.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QDoubleSpinBox,
    QFrame, QHeaderView, QLabel, QMainWindow,
    QPlainTextEdit, QPushButton, QSizePolicy, QSpinBox,
    QStatusBar, QTableWidget, QTableWidgetItem, QWidget)

class Ui_observe(object):
    def setupUi(self, observe):
        if not observe.objectName():
            observe.setObjectName(u"observe")
        observe.resize(1569, 242)
        self.actionSelect_Script = QAction(observe)
        self.actionSelect_Script.setObjectName(u"actionSelect_Script")
        self.centralwidget = QWidget(observe)
        self.centralwidget.setObjectName(u"centralwidget")
        self.tableWidget_script = QTableWidget(self.centralwidget)
        if (self.tableWidget_script.columnCount() < 17):
            self.tableWidget_script.setColumnCount(17)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget_script.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget_script.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableWidget_script.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableWidget_script.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableWidget_script.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tableWidget_script.setHorizontalHeaderItem(5, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.tableWidget_script.setHorizontalHeaderItem(6, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.tableWidget_script.setHorizontalHeaderItem(7, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.tableWidget_script.setHorizontalHeaderItem(8, __qtablewidgetitem8)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.tableWidget_script.setHorizontalHeaderItem(9, __qtablewidgetitem9)
        __qtablewidgetitem10 = QTableWidgetItem()
        self.tableWidget_script.setHorizontalHeaderItem(10, __qtablewidgetitem10)
        __qtablewidgetitem11 = QTableWidgetItem()
        self.tableWidget_script.setHorizontalHeaderItem(11, __qtablewidgetitem11)
        __qtablewidgetitem12 = QTableWidgetItem()
        self.tableWidget_script.setHorizontalHeaderItem(12, __qtablewidgetitem12)
        __qtablewidgetitem13 = QTableWidgetItem()
        self.tableWidget_script.setHorizontalHeaderItem(13, __qtablewidgetitem13)
        __qtablewidgetitem14 = QTableWidgetItem()
        self.tableWidget_script.setHorizontalHeaderItem(14, __qtablewidgetitem14)
        __qtablewidgetitem15 = QTableWidgetItem()
        self.tableWidget_script.setHorizontalHeaderItem(15, __qtablewidgetitem15)
        __qtablewidgetitem16 = QTableWidgetItem()
        self.tableWidget_script.setHorizontalHeaderItem(16, __qtablewidgetitem16)
        if (self.tableWidget_script.rowCount() < 1):
            self.tableWidget_script.setRowCount(1)
        __qtablewidgetitem17 = QTableWidgetItem()
        self.tableWidget_script.setItem(0, 1, __qtablewidgetitem17)
        self.tableWidget_script.setObjectName(u"tableWidget_script")
        self.tableWidget_script.setGeometry(QRect(10, 120, 1551, 61))
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableWidget_script.sizePolicy().hasHeightForWidth())
        self.tableWidget_script.setSizePolicy(sizePolicy)
        self.tableWidget_script.setMinimumSize(QSize(50, 50))
        font = QFont()
        font.setPointSize(5)
        self.tableWidget_script.setFont(font)
        self.tableWidget_script.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tableWidget_script.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tableWidget_script.setAutoScroll(True)
        self.tableWidget_script.setAlternatingRowColors(True)
        self.tableWidget_script.setVerticalScrollMode(QAbstractItemView.ScrollPerItem)
        self.tableWidget_script.setHorizontalScrollMode(QAbstractItemView.ScrollPerItem)
        self.tableWidget_script.setRowCount(1)
        self.tableWidget_script.setColumnCount(17)
        self.tableWidget_script.horizontalHeader().setMinimumSectionSize(30)
        self.tableWidget_script.horizontalHeader().setDefaultSectionSize(90)
        self.tableWidget_script.horizontalHeader().setStretchLastSection(False)
        self.tableWidget_script.verticalHeader().setVisible(False)
        self.tableWidget_script.verticalHeader().setMinimumSectionSize(11)
        self.tableWidget_script.verticalHeader().setDefaultSectionSize(10)
        self.tableWidget_script.verticalHeader().setStretchLastSection(False)
        self.pushButton_run = QPushButton(self.centralwidget)
        self.pushButton_run.setObjectName(u"pushButton_run")
        self.pushButton_run.setGeometry(QRect(110, 50, 81, 31))
        font1 = QFont()
        font1.setBold(True)
        self.pushButton_run.setFont(font1)
        self.pushButton_abort_script = QPushButton(self.centralwidget)
        self.pushButton_abort_script.setObjectName(u"pushButton_abort_script")
        self.pushButton_abort_script.setGeometry(QRect(650, 50, 101, 31))
        font2 = QFont()
        font2.setBold(False)
        self.pushButton_abort_script.setFont(font2)
        self.pushButton_abort_script.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(255, 112, 114);\n"
"}\n"
"")
        self.spinBox_loops = QSpinBox(self.centralwidget)
        self.spinBox_loops.setObjectName(u"spinBox_loops")
        self.spinBox_loops.setGeometry(QRect(250, 50, 41, 31))
        self.spinBox_loops.setMinimum(1)
        self.label_loops = QLabel(self.centralwidget)
        self.label_loops.setObjectName(u"label_loops")
        self.label_loops.setGeometry(QRect(200, 50, 51, 30))
        self.plainTextEdit_filename = QPlainTextEdit(self.centralwidget)
        self.plainTextEdit_filename.setObjectName(u"plainTextEdit_filename")
        self.plainTextEdit_filename.setGeometry(QRect(10, 10, 721, 31))
        self.pushButton_selectscript = QPushButton(self.centralwidget)
        self.pushButton_selectscript.setObjectName(u"pushButton_selectscript")
        self.pushButton_selectscript.setGeometry(QRect(760, 10, 101, 31))
        self.label_status = QLabel(self.centralwidget)
        self.label_status.setObjectName(u"label_status")
        self.label_status.setGeometry(QRect(10, 90, 1551, 20))
        self.label_status.setStyleSheet(u"QLabel {\n"
"    background-color: rgb(199, 199, 199);\n"
"}\n"
"")
        self.label_status.setFrameShape(QFrame.StyledPanel)
        self.label_status.setFrameShadow(QFrame.Sunken)
        self.pushButton_loadscript = QPushButton(self.centralwidget)
        self.pushButton_loadscript.setObjectName(u"pushButton_loadscript")
        self.pushButton_loadscript.setGeometry(QRect(10, 50, 91, 31))
        self.label_counter = QLabel(self.centralwidget)
        self.label_counter.setObjectName(u"label_counter")
        self.label_counter.setGeometry(QRect(860, 50, 31, 31))
        self.label_counter.setFont(font1)
        self.label_counter.setFrameShape(QFrame.StyledPanel)
        self.label_counter.setFrameShadow(QFrame.Sunken)
        self.label_counter.setAlignment(Qt.AlignCenter)
        self.pushButton_pause_script = QPushButton(self.centralwidget)
        self.pushButton_pause_script.setObjectName(u"pushButton_pause_script")
        self.pushButton_pause_script.setGeometry(QRect(520, 50, 121, 31))
        self.pushButton_pause_script.setFont(font2)
        self.pushButton_pause_script.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(255, 255, 127);\n"
"}\n"
"")
        self.pushButton_editscript = QPushButton(self.centralwidget)
        self.pushButton_editscript.setObjectName(u"pushButton_editscript")
        self.pushButton_editscript.setGeometry(QRect(760, 50, 91, 31))
        self.doubleSpinBox_ExpTimeScale = QDoubleSpinBox(self.centralwidget)
        self.doubleSpinBox_ExpTimeScale.setObjectName(u"doubleSpinBox_ExpTimeScale")
        self.doubleSpinBox_ExpTimeScale.setGeometry(QRect(370, 50, 62, 30))
        self.doubleSpinBox_ExpTimeScale.setDecimals(3)
        self.doubleSpinBox_ExpTimeScale.setValue(1.000000000000000)
        self.label_loops_2 = QLabel(self.centralwidget)
        self.label_loops_2.setObjectName(u"label_loops_2")
        self.label_loops_2.setGeometry(QRect(300, 50, 71, 30))
        self.pushButton_scale_et = QPushButton(self.centralwidget)
        self.pushButton_scale_et.setObjectName(u"pushButton_scale_et")
        self.pushButton_scale_et.setGeometry(QRect(440, 50, 71, 31))
        self.pushButton_scale_et.setFont(font2)
        self.pushButton_scale_et.setStyleSheet(u"")
        self.checkBox_azalt = QCheckBox(self.centralwidget)
        self.checkBox_azalt.setObjectName(u"checkBox_azalt")
        self.checkBox_azalt.setEnabled(True)
        self.checkBox_azalt.setGeometry(QRect(900, 50, 111, 30))
        observe.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(observe)
        self.statusbar.setObjectName(u"statusbar")
        observe.setStatusBar(self.statusbar)

        self.retranslateUi(observe)

        QMetaObject.connectSlotsByName(observe)
    # setupUi

    def retranslateUi(self, observe):
        observe.setWindowTitle(QCoreApplication.translate("observe", u"Observe", None))
        self.actionSelect_Script.setText(QCoreApplication.translate("observe", u"Select Script", None))
        ___qtablewidgetitem = self.tableWidget_script.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("observe", u"#", None));
        ___qtablewidgetitem1 = self.tableWidget_script.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("observe", u"Status", None));
#if QT_CONFIG(tooltip)
        ___qtablewidgetitem1.setToolTip(QCoreApplication.translate("observe", u"# => do not execute", None));
#endif // QT_CONFIG(tooltip)
        ___qtablewidgetitem2 = self.tableWidget_script.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("observe", u"Command", None));
        ___qtablewidgetitem3 = self.tableWidget_script.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("observe", u"Args", None));
        ___qtablewidgetitem4 = self.tableWidget_script.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("observe", u"ExpTime", None));
        ___qtablewidgetitem5 = self.tableWidget_script.horizontalHeaderItem(5)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("observe", u"Type", None));
        ___qtablewidgetitem6 = self.tableWidget_script.horizontalHeaderItem(6)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("observe", u"Title", None));
        ___qtablewidgetitem7 = self.tableWidget_script.horizontalHeaderItem(7)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("observe", u"NumExps", None));
        ___qtablewidgetitem8 = self.tableWidget_script.horizontalHeaderItem(8)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("observe", u"Filter", None));
        ___qtablewidgetitem9 = self.tableWidget_script.horizontalHeaderItem(9)
        ___qtablewidgetitem9.setText(QCoreApplication.translate("observe", u"RA", None));
        ___qtablewidgetitem10 = self.tableWidget_script.horizontalHeaderItem(10)
        ___qtablewidgetitem10.setText(QCoreApplication.translate("observe", u"DEC", None));
        ___qtablewidgetitem11 = self.tableWidget_script.horizontalHeaderItem(11)
        ___qtablewidgetitem11.setText(QCoreApplication.translate("observe", u"Epoch", None));
        ___qtablewidgetitem12 = self.tableWidget_script.horizontalHeaderItem(12)
        ___qtablewidgetitem12.setText(QCoreApplication.translate("observe", u"EXPOSE", None));
        ___qtablewidgetitem13 = self.tableWidget_script.horizontalHeaderItem(13)
        ___qtablewidgetitem13.setText(QCoreApplication.translate("observe", u"MOVETEL", None));
        ___qtablewidgetitem14 = self.tableWidget_script.horizontalHeaderItem(14)
        ___qtablewidgetitem14.setText(QCoreApplication.translate("observe", u"STEPTEL", None));
        ___qtablewidgetitem15 = self.tableWidget_script.horizontalHeaderItem(15)
        ___qtablewidgetitem15.setText(QCoreApplication.translate("observe", u"MOVFILTER", None));
        ___qtablewidgetitem16 = self.tableWidget_script.horizontalHeaderItem(16)
        ___qtablewidgetitem16.setText(QCoreApplication.translate("observe", u"MOVFOCUS", None));

        __sortingEnabled = self.tableWidget_script.isSortingEnabled()
        self.tableWidget_script.setSortingEnabled(False)
        self.tableWidget_script.setSortingEnabled(__sortingEnabled)

#if QT_CONFIG(tooltip)
        self.tableWidget_script.setToolTip(QCoreApplication.translate("observe", u"script command table", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.pushButton_run.setToolTip(QCoreApplication.translate("observe", u"execute the script", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_run.setText(QCoreApplication.translate("observe", u"Run", None))
#if QT_CONFIG(tooltip)
        self.pushButton_abort_script.setToolTip(QCoreApplication.translate("observe", u"<html><head/><body><p>abort script execution as soon as possible</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_abort_script.setText(QCoreApplication.translate("observe", u"Abort Script", None))
#if QT_CONFIG(tooltip)
        self.spinBox_loops.setToolTip(QCoreApplication.translate("observe", u"<html><head/><body><p>Number of times to run the complete script</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_loops.setText(QCoreApplication.translate("observe", u"Cycles", None))
        self.plainTextEdit_filename.setPlainText(QCoreApplication.translate("observe", u"C:/azcam/systems/90prime6/ObservingScripts/test.txt", None))
#if QT_CONFIG(tooltip)
        self.pushButton_selectscript.setToolTip(QCoreApplication.translate("observe", u"select a script on disk", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_selectscript.setText(QCoreApplication.translate("observe", u"Select Script", None))
        self.label_status.setText("")
#if QT_CONFIG(tooltip)
        self.pushButton_loadscript.setToolTip(QCoreApplication.translate("observe", u"load the script into the table below", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_loadscript.setText(QCoreApplication.translate("observe", u"Load Script", None))
#if QT_CONFIG(tooltip)
        self.label_counter.setToolTip(QCoreApplication.translate("observe", u"watchdog", None))
#endif // QT_CONFIG(tooltip)
        self.label_counter.setText("")
#if QT_CONFIG(tooltip)
        self.pushButton_pause_script.setToolTip(QCoreApplication.translate("observe", u"<html><head/><body><p>Pause/Resume a running script (toggle)</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_pause_script.setText(QCoreApplication.translate("observe", u"Pause/Resume", None))
#if QT_CONFIG(tooltip)
        self.pushButton_editscript.setToolTip(QCoreApplication.translate("observe", u"edit the script file", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_editscript.setText(QCoreApplication.translate("observe", u"Edit Script", None))
#if QT_CONFIG(tooltip)
        self.doubleSpinBox_ExpTimeScale.setToolTip(QCoreApplication.translate("observe", u"scale to apply to all exposure times", None))
#endif // QT_CONFIG(tooltip)
        self.label_loops_2.setText(QCoreApplication.translate("observe", u"ET Scale", None))
#if QT_CONFIG(tooltip)
        self.pushButton_scale_et.setToolTip(QCoreApplication.translate("observe", u"<html><head/><body><p>Pause/Resume a running script (toggle)</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.pushButton_scale_et.setStatusTip(QCoreApplication.translate("observe", u"apply ET Scale to exposure time", None))
#endif // QT_CONFIG(statustip)
        self.pushButton_scale_et.setText(QCoreApplication.translate("observe", u"Scale ET", None))
#if QT_CONFIG(statustip)
        self.checkBox_azalt.setStatusTip(QCoreApplication.translate("observe", u"Check for Az/Alt instead of RA/Dec", None))
#endif // QT_CONFIG(statustip)
        self.checkBox_azalt.setText(QCoreApplication.translate("observe", u"Use Alt/Az?", None))
    # retranslateUi

