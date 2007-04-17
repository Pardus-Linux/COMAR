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

from qt import *

import ldapmodel


class Item(QListViewItem):
    def __init__(self, tree, item, parent=None):
        if parent:
            QListViewItem.__init__(self, parent)
        else:
            QListViewItem.__init__(self, tree)
        self.item = item
        self.setExpandable(True)
    
    def text(self, col):
        return self.item.name
    
    def insertDC(self, name):
        self.item.insertDC(name)


class Browser(QListView):
    def __init__(self, parent):
        QListView.__init__(self, parent)
        self.addColumn("")
        self.header().hide()
        self.setRootIsDecorated(True)
        
        self.connect(self, SIGNAL("expanded(QListViewItem*)"), self.slotExpand)
        
        Item(self, ldapmodel.Domain("Test"))
    
    def slotExpand(self, item):
        for kid in item.item.expand():
            Item(self, kid, item)
