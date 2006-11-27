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


class ClassItem(QListViewItem):
    def __init__(self, parent, group_name, tag):
        QListViewItem.__init__(self, parent)
        self.group = group_name
        self.name = tag.getAttribute("name")
        self.setText(0, "%s.%s" % (self.group, self.name))
        self.methods = []
        for item in tag.tags("method"):
            self.methods.append(item.getAttribute("name"))


class ModelView(QHBox):
    def __init__(self, parent):
        QHBox.__init__(self, parent)
        self.setSpacing(6)
        
        self.classes = QListView(self)
        self.classes.addColumn("Classes")
        self.classes.setAllColumnsShowFocus(True)
        self.classes.setSorting(-1)
        self.connect(self.classes, SIGNAL("selectionChanged()"), self.slotClass)
        
        self.methods = QListView(self)
        self.methods.addColumn("Methods")
        self.methods.setAllColumnsShowFocus(True)
        self.methods.setSorting(-1)
        self.connect(self.methods, SIGNAL("selectionChanged()"), self.slotMethod)
        
        self.load("/etc/comar/model.xml")
    
    def load(self, modelfile):
        doc = piksemel.parse(modelfile)
        for group in doc.tags("group"):
            name = group.getAttribute("name")
            for class_ in group.tags("class"):
                ClassItem(self.classes, name, class_)
    
    def slotClass(self):
        item = self.classes.selectedItem()
        self.methods.clear()
        if item:
            for name in item.methods:
                QListViewItem(self.methods, name)
    
    def slotMethod(self):
        pass


class MainWindow(KMainWindow):
    def __init__(self):
        KMainWindow.__init__(self)
        self.setMinimumSize(560, 440)
        self.setCaption(u"Çomar Model Tool")
        
        mb = self.menuBar()
        file_ = QPopupMenu(self)
        mb.insertItem("&File", file_)
        file_.insertItem("&Open", self.slotOpen, self.CTRL + self.Key_O)
        file_.insertItem("&Save", self.slotSave, self.CTRL + self.Key_S)
        file_.insertItem("Save &as...", self.slotSaveAs, self.CTRL + self.SHIFT + self.Key_S)
        file_.insertSeparator()
        file_.insertItem("&Quit", self.quit, self.CTRL + self.Key_Q)
        
        self.model = ModelView(self)
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
        I18N_NOOP("Comar Model Tool"),
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
