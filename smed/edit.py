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
from enums import *


class Argument(QListViewItem):
    def __init__(self, list, name, is_instance):
        QListViewItem.__init__(self, list)
        self.name = name
        self.is_instance = is_instance
    
    def text(self, col):
        if col == 0:
            return self.name
        else:
            if self.is_instance:
                return "+"
            else:
                return ""


class NodeEdit(QWidget):
    def __init__(self, *args):
        QWidget.__init__(self, *args)
        vb = QVBoxLayout(self)
        vb.setSpacing(6)
        vb.setMargin(6)

        hb = QHBoxLayout(vb)
        lab = QLabel("Name:", self)
        hb.addWidget(lab)
        self.name = QLineEdit(self)
        hb.addWidget(self.name)
        self.connect(self.name, SIGNAL("textChanged(const QString &)"), self._slotName)

        hb = QHBoxLayout(vb)
        lab = QLabel("Profile mode:", self)
        hb.addWidget(lab)
        self.profile = QComboBox(False, self)
        self.connect(self.profile, SIGNAL("activated(int)"), self._slotProfile)
        self.profile.insertItem("None", NONE)
        self.profile.insertItem("Global", GLOBAL)
        self.profile.insertItem("Package", PACKAGE)
        hb.addWidget(self.profile)
        hb.addStretch(1)
        
        vb2 = QVBoxLayout(vb)
        vb2.setSpacing(2)
        
        self.args = QListView(self)
        vb2.addWidget(self.args)
        self.args.setSorting(-1)
        self.args.addColumn("Argument")
        self.args.addColumn("instance?")
        
        hb = QHBox(self)
        self.buttons = hb
        vb2.addWidget(hb)
        but = QPushButton("Add argument", hb)
        self.connect(but, SIGNAL("clicked()"), self._slotArgument)
        but = QPushButton("Add instance", hb)
        self.connect(but, SIGNAL("clicked()"), self._slotInstance)
        
        lab = QLabel("Description:", self)
        vb.addWidget(lab)
        self.desc = QTextEdit(self)
        vb.addWidget(self.desc)
        self.connect(self.desc, SIGNAL("textChanged()"), self._slotDesc)
        self.node = None
    
    def _slotArgument(self):
        result =  QInputDialog.getText("SMED", "Enter argument name:", QLineEdit.Normal, "", self)
        if result[1] and result[0] != "":
            Argument(self.args, result[0], False)
            self.node.nodeArguments.append((result[0], False))
    
    def _slotInstance(self):
        result =  QInputDialog.getText("SMED", "Enter instance name:", QLineEdit.Normal, "", self)
        if result[1] and result[0] != "":
            Argument(self.args, result[0], True)
            self.node.nodeArguments.append((result[0], True))
    
    def _slotProfile(self, no):
        if self.node:
            self.node.nodeProfile = no
    
    def _slotName(self, text):
        if self.node:
            self.node.nodeName = unicode(self.name.text())
            self.node.repaint()
    
    def _slotDesc(self):
        if self.node:
            self.node.nodeDesc = unicode(self.desc.text())
    
    def use_node(self, node):
        self.node = None
        self.name.setText(node.nodeName)
        self.desc.setText(node.nodeDesc)
        self.args.clear()
        for item in node.nodeArguments:
            Argument(self.args, item[0], item[1])
        if node.nodeType == METHOD:
            self.profile.setCurrentItem(node.nodeProfile)
            self.profile.setEnabled(True)
            self.buttons.setEnabled(True)
            self.args.setEnabled(True)
        else:
            self.profile.setEnabled(False)
            self.buttons.setEnabled(False)
            self.args.setEnabled(False)
        self.node = node
