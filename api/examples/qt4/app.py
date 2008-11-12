#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import comar
import mainform

from PyQt4 import QtGui
from PyQt4.QtCore import *

from dbus.mainloop.qt import DBusQtMainLoop

class Window(QtGui.QWidget):
    def __init__(self, *args):
        QtGui.QWidget.__init__(self, None)

        # Create ui
        self.ui = mainform.Ui_mainForm()
        self.ui.setupUi(self)

        # Call Comar
        self.link = comar.Link()

        # Connect button click event to getServices method
        self.connect(self.ui.buttonServices, SIGNAL("clicked()"), self.getServices)

    def handleServices(self, package, exception, results):
        # Handle request and fill the textEdit in ui
        if not exception:
            serviceName, serviceDesc, serviceState = results
            self.ui.textServices.append("%s - %s - %s - %s" % (package, serviceName, serviceDesc, serviceState))

    def getServices(self):
        # Get service list from comar link
        self.link.System.Service.info(async=self.handleServices)

def main():
    app = QtGui.QApplication(sys.argv)

    DBusQtMainLoop(set_as_default = True)

    win = Window()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
