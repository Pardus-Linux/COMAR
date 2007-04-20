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

import os
from qt import *
import piksemel

import ldapmodel


class BrowserItem(QListViewItem):
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
        
        self.load()
    
    def slotExpand(self, item):
        kid = item.firstChild()
        while kid:
            tmp = kid.nextSibling()
            item.takeItem(kid)
            kid = tmp
        for kid in item.item.expand():
            BrowserItem(self, kid, item)
    
    def configFile(self):
        return os.path.join(os.getenv("HOME"), ".ahenk-lider.xml")
    
    def load(self):
        path = self.configFile()
        if os.path.exists(path):
            doc = piksemel.parse(path)
            for tag in doc.getTag("Domains").tags("Domain"):
                dom = ldapmodel.Domain()
                dom.fromXML(tag)
                BrowserItem(self, dom)
    
    def save(self):
        path = self.configFile()
        doc = piksemel.newDocument("AhenkLider")
        doms = doc.insertTag("Domains")
        item = self.firstChild()
        while item:
            doms.insertNode(item.item.toXML())
            item = item.nextSibling()
        file(path, "w").write(doc.toPrettyString())


class ObjectItem(QListViewItem):
    def __init__(self, tree, item):
        QListViewItem.__init__(self, tree)
        self.item = item
    
    def text(self, col):
        return self.item.name


class Objects(QListView):
    def __init__(self, parent):
        QListView.__init__(self, parent)
        self.addColumn("")
