#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

import sys
from qt import *
import model

class MainWindow(QMainWindow):
    def __init__(self, *args):
        QMainWindow.__init__(self, *args)
        self.model = model.Model(self)
        self.setCaption(u"ÇOMAR System Model Editor")
        self.setMinimumSize(600, 440)
        mb = self.menuBar()
        file_ = QPopupMenu(self)
        mb.insertItem("&File", file_)
        file_.insertItem("&Open", self.model.open, self.CTRL + self.Key_O)
        file_.insertItem("&Save", self.model.save, self.CTRL + self.Key_S)
        file_.insertItem("Save &as...", self.model.save_as, self.CTRL + self.SHIFT + self.Key_S)
        file_.insertSeparator()
        file_.insertItem("&Quit", main_quit, self.CTRL + self.Key_Q)
        self.setCentralWidget(self.model)

def main_quit():
    sys.exit(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.connect(app, SIGNAL("lastWindowClosed()"), main_quit)
    w = MainWindow()
    w.show()
    if len(sys.argv) > 1:
        w.model.open_as(sys.argv[1])
    else:
        w.model.clear()
    app.exec_loop()
