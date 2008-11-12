#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from qt import *

import comar
from dbus.mainloop.qt3 import DBusQtMainLoop

import mainform

class Window(mainform.mainForm):
    def __init__(self, parent=None):
        mainform.mainForm.__init__(self, parent)

        self.link = comar.Link()

        self.connect(self.buttonServices, SIGNAL("clicked()"), self.getServices)

    def handleServices(self, package, exception, results):
        if not exception:
            serviceName, serviceDesc, serviceState = results
            self.textServices.append("%s - %s - %s - %s" % (package, serviceName, serviceDesc, serviceState))

    def getServices(self):
        self.link.System.Service.info(async=self.handleServices)

def main():
    app = QApplication(sys.argv)

    # Attach DBus to main loop
    DBusQtMainLoop(set_as_default=True)

    app.connect(app, SIGNAL("lastWindowClosed()"), app, SLOT("quit()"))

    win = Window()
    win.show()

    # Enter main loop
    app.exec_loop()

if __name__ == "__main__":
    main()
