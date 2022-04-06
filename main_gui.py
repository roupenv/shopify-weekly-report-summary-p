# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_gui.ui'
##
## Created by: Qt User Interface Compiler version 5.15.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import (QCoreApplication, QDate, QDateTime, QMetaObject,
    QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QKeySequence, QLinearGradient, QPalette, QPainter,
    QPixmap, QRadialGradient)
from PySide2.QtWidgets import *


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(752, 463)
        self.actionFile = QAction(MainWindow)
        self.actionFile.setObjectName(u"actionFile")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.title = QLabel(self.centralwidget)
        self.title.setObjectName(u"title")
        self.title.setGeometry(QRect(110, 10, 521, 31))
        font = QFont()
        font.setPointSize(20)
        self.title.setFont(font)
        self.title.setAlignment(Qt.AlignCenter)
        self.layoutWidget = QWidget(self.centralwidget)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(310, 370, 116, 44))
        self.verticalLayout_4 = QVBoxLayout(self.layoutWidget)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.line_3 = QFrame(self.layoutWidget)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_4.addWidget(self.line_3)

        self.exit = QPushButton(self.layoutWidget)
        self.exit.setObjectName(u"exit")

        self.verticalLayout_4.addWidget(self.exit)

        self.layoutWidget1 = QWidget(self.centralwidget)
        self.layoutWidget1.setObjectName(u"layoutWidget1")
        self.layoutWidget1.setGeometry(QRect(50, 60, 645, 212))
        self.horizontalLayout = QHBoxLayout(self.layoutWidget1)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(self.layoutWidget1)
        self.label.setObjectName(u"label")
        font1 = QFont()
        font1.setPointSize(12)
        self.label.setFont(font1)
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.start_date = QCalendarWidget(self.layoutWidget1)
        self.start_date.setObjectName(u"start_date")

        self.verticalLayout.addWidget(self.start_date)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.line = QFrame(self.layoutWidget1)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout.addWidget(self.line)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.splitter = QSplitter(self.layoutWidget1)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.label_2 = QLabel(self.splitter)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font1)
        self.label_2.setAlignment(Qt.AlignCenter)
        self.splitter.addWidget(self.label_2)

        self.verticalLayout_2.addWidget(self.splitter)

        self.end_date = QCalendarWidget(self.layoutWidget1)
        self.end_date.setObjectName(u"end_date")
        self.end_date.setGridVisible(False)

        self.verticalLayout_2.addWidget(self.end_date)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.layoutWidget2 = QWidget(self.centralwidget)
        self.layoutWidget2.setObjectName(u"layoutWidget2")
        self.layoutWidget2.setGeometry(QRect(210, 280, 318, 32))
        self.horizontalLayout_2 = QHBoxLayout(self.layoutWidget2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.run_orders = QPushButton(self.layoutWidget2)
        self.run_orders.setObjectName(u"run_orders")

        self.horizontalLayout_2.addWidget(self.run_orders)

        self.run_refunds = QPushButton(self.layoutWidget2)
        self.run_refunds.setObjectName(u"run_refunds")

        self.horizontalLayout_2.addWidget(self.run_refunds)

        self.clear_cache = QPushButton(self.centralwidget)
        self.clear_cache.setObjectName(u"clear_cache")
        self.clear_cache.setGeometry(QRect(320, 330, 101, 21))
        self.layoutWidget3 = QWidget(self.centralwidget)
        self.layoutWidget3.setObjectName(u"layoutWidget3")
        self.layoutWidget3.setGeometry(QRect(560, 320, 189, 68))
        self.horizontalLayout_3 = QHBoxLayout(self.layoutWidget3)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.line_2 = QFrame(self.layoutWidget3)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.VLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_3.addWidget(self.line_2)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.update_transaction = QPushButton(self.layoutWidget3)
        self.update_transaction.setObjectName(u"update_transaction")

        self.verticalLayout_3.addWidget(self.update_transaction)

        self.clear_transactions = QPushButton(self.layoutWidget3)
        self.clear_transactions.setObjectName(u"clear_transactions")

        self.verticalLayout_3.addWidget(self.clear_transactions)


        self.horizontalLayout_3.addLayout(self.verticalLayout_3)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 752, 21))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        QWidget.setTabOrder(self.start_date, self.end_date)
        QWidget.setTabOrder(self.end_date, self.run_orders)
        QWidget.setTabOrder(self.run_orders, self.run_refunds)
        QWidget.setTabOrder(self.run_refunds, self.clear_cache)
        QWidget.setTabOrder(self.clear_cache, self.update_transaction)
        QWidget.setTabOrder(self.update_transaction, self.clear_transactions)
        QWidget.setTabOrder(self.clear_transactions, self.exit)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionFile.setText(QCoreApplication.translate("MainWindow", u"File", None))
        self.title.setText(QCoreApplication.translate("MainWindow", u"REPORT GENERATOR", None))
        self.exit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Select Start Date", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Select End Date", None))
        self.run_orders.setText(QCoreApplication.translate("MainWindow", u"Run Orders Report", None))
        self.run_refunds.setText(QCoreApplication.translate("MainWindow", u"Run Refunds Report", None))
        self.clear_cache.setText(QCoreApplication.translate("MainWindow", u"Clear Cache", None))
        self.update_transaction.setText(QCoreApplication.translate("MainWindow", u"Get New Payouts", None))
        self.clear_transactions.setText(QCoreApplication.translate("MainWindow", u"Clear Payouts", None))
    # retranslateUi

