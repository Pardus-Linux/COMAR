#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

import os
import sys
import piksemel
from qt import *
from kdecore import *
from kdeui import *

I18N_NOOP = lambda x: x

def getIconSet(name, group=KIcon.Toolbar):
    return KGlobal.iconLoader().loadIconSet(name, group)


class Model(QListView):
    def __init__(self, parent):
        QListView.__init__(self, parent)
        self.addColumn("")
        self.addColumn("")
        self.header().hide()
        self.setTreeStepSize(self.treeStepSize() * 1.2)
        self.setSorting(-1)
        self.load("/etc/comar/model.xml")
    
    def load(self, modelfile):
        doc = piksemel.parse(modelfile)
        for group_tag in doc.tags("group"):
            group = QListViewItem(self)
            group.setPixmap(0, getIconSet("kwikdisk.png").pixmap(QIconSet.Automatic, QIconSet.Normal))
            group.setText(1, group_tag.getAttribute("name"))
            group.setOpen(True)
            for class_tag in group_tag.tags("class"):
                class_ = QListViewItem(group)
                class_.setPixmap(0, getIconSet("kuser.png").pixmap(QIconSet.Automatic, QIconSet.Normal))
                class_.setText(1, class_tag.getAttribute("name"))
                class_.setOpen(True)
                for method_tag in class_tag.tags("method"):
                    method = QListViewItem(class_)
                    method.setPixmap(0, getIconSet("kservices.png").pixmap(QIconSet.Automatic, QIconSet.Normal))
                    method.setText(1, method_tag.getAttribute("name"))
                    method.setOpen(True)
                for notify_tag in class_tag.tags("notify"):
                    notify = QListViewItem(class_)
                    notify.setPixmap(0, getIconSet("remote.png").pixmap(QIconSet.Automatic, QIconSet.Normal))
                    notify.setText(1, notify_tag.getAttribute("name"))
                    notify.setOpen(True)


class MainWindow(KMainWindow):
    def __init__(self):
        KMainWindow.__init__(self)
        self.setMinimumSize(560, 440)
        self.setCaption(u"ÇOMAR System Model Editor")
        
        mb = self.menuBar()
        file_ = QPopupMenu(self)
        mb.insertItem("&File", file_)
        file_.insertItem("&Open", self.slotOpen, self.CTRL + self.Key_O)
        file_.insertItem("&Save", self.slotSave, self.CTRL + self.Key_S)
        file_.insertItem("Save &as...", self.slotSaveAs, self.CTRL + self.SHIFT + self.Key_S)
        file_.insertSeparator()
        file_.insertItem("&Quit", self.quit, self.CTRL + self.Key_Q)
        
        self.model = Model(self)
        self.setCentralWidget(self.model)
    
    def quit(self):
        KApplication.kApplication().closeAllWindows()
    
    def slotOpen(self):
        pass
    
    def slotSave(self):
        pass
    
    def slotSaveAs(self):
        pass


def main(args):
    about = KAboutData(
        "comodel",
        "Comodel",
        "1.0",
        I18N_NOOP("Pardus distribution media maker"),
        KAboutData.License_GPL
    )
    KCmdLineArgs.init(args, about)
    app = KApplication()
    app.connect(app, SIGNAL("lastWindowClosed()"), app, SLOT("quit()"))
    w = MainWindow()
    w.show()
    app.exec_loop()

if __name__ == "__main__":
    main(sys.argv[:])
