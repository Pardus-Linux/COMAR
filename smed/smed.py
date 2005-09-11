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
        self.setCaption(u"ÇOMAR System Model Editor")
        self.setMinimumSize(540,320)
        mb = self.menuBar()
        file_ = QPopupMenu(self)
        mb.insertItem("&File", file_)
        file_.insertItem("&Open", self._cb_open, self.CTRL + self.Key_O)
        file_.insertItem("&Save", self._cb_save, self.CTRL + self.Key_S)
        file_.insertItem("Save &as...", self._cb_save_as, self.CTRL + self.SHIFT + self.Key_S)
        file_.insertSeparator()
        file_.insertItem("&Quit", main_quit, self.CTRL + self.Key_Q)
        self.model = model.Model(self)
        self.setCentralWidget(self.model)
        self.fileName = None
    
    def _cb_open(self):
        name = QFileDialog.getOpenFileName(".", "Model Files (*.xml)", self, "lala", "Choose model file to open")
        if not name:
            return
        name = unicode(name)
        w.model.load(name)
        self.fileName = name
    
    def _cb_save_as(self):
        name = QFileDialog.getSaveFileName(".", "Model Files (*.xml)", self, "lala", "Choose model file to save")
        if not name:
            return
        name = unicode(name)
        w.model.save(name)
        self.fileName = name
    
    def _cb_save(self):
        if self.fileName:
            w.model.save(self.fileName)
        else:
            self._cb_save_as()

def main_quit():
    sys.exit(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.connect(app, SIGNAL("lastWindowClosed()"), main_quit)
    w = MainWindow()
    w.show()
    w.model.clear()
    app.exec_loop()
