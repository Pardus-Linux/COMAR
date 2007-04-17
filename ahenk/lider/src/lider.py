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


def main(args):
    desc = I18N_NOOP("Pardus Management Console")
    version = "0.1"
    
    about = KAboutData(
        "lider",
        "Lider",
        version,
        desc,
        KAboutData.License_GPL,
    )
    KCmdLineArgs.init(args, about)
    
    app = KApplication()
    app.connect(app, SIGNAL("lastWindowClosed()"), app, SLOT("quit()"))
    
    w = mainwindow.MainWindow()
    w.show()
    
    app.exec_loop()


if __name__ == "__main__":
    main(sys.argv[:])
