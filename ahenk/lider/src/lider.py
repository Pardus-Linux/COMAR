#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

import sys
from qt import *
from kdecore import *

import mainwindow
from utility import *

version = "0.1"

def aboutData():
    about = KAboutData("lider",
                       "Lider",
                       version,
                       I18N_NOOP("Pardus Management Console"),
                       KAboutData.License_GPL,
                       "(C) 2007 TÜBİTAK/UEKAE",
                       None,
                       None,
                       "bugs@pardus.org.tr")
    return about

def main(args):
    about = aboutData()
    KCmdLineArgs.init(args, about)
    
    app = KApplication()
    app.connect(app, SIGNAL("lastWindowClosed()"), app, SLOT("quit()"))
    
    w = mainwindow.MainWindow(app)
    w.show()
    
    app.exec_loop()


if __name__ == "__main__":
    main(sys.argv[:])
