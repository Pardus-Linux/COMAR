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

from qt import *

class NodeEdit(QWidget):
    def __init__(self, *args):
        QWidget.__init__(self, *args)
        vb = QVBoxLayout(self)
        lab = QLabel("Name:", self)
        vb.addWidget(lab)
        self.name = QLineEdit(self)
        vb.addWidget(self.name)
        self.connect(self.name, SIGNAL("textChanged(const QString &)"), self._name_cb)
        lab = QLabel("Description:", self)
        vb.addWidget(lab)
        self.desc = QTextEdit(self)
        vb.addWidget(self.desc)
        self.connect(self.desc, SIGNAL("textChanged()"), self._desc_cb)
        self.node = None
    
    def _name_cb(self, text):
        if self.node:
            self.node.nodeName = unicode(self.name.text())
    
    def _desc_cb(self):
        if self.node:
            self.node.nodeDesc = unicode(self.desc.text())
    
    def use_node(self, node):
        self.node = None
        self.name.setText(node.nodeName)
        self.desc.setText(node.nodeDesc)
        self.node = node
