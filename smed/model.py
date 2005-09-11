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
import xml.dom.minidom as mdom
import codecs

import edit

def getByName(parent, childName):
    return [x for x in parent.childNodes if x.nodeType == x.ELEMENT_NODE if x.tagName == childName]

def get_cdata(node, tag):
    try:
        c = getByName(node, tag)[0].firstChild.data
    except:
        c = ""
    return c

class Node(QListViewItem):
    MODEL = 0
    CLASS = 1
    GROUP = 2
    METHOD = 3

    def __init__(self, parent, type, name, data=None):
        QListViewItem.__init__(self, parent, name)
        self.nodeParent = parent
        self.nodeType = type
        self.nodeName = name
        if data is not None:
            tmp = get_cdata(data, "description")
            if tmp == "":
                self.nodeDesc = ""
            else:
                tmp = tmp.strip(' \n')
                tmp = tmp.split('\n')
                L1 = len([x for x in tmp[0] if x == '\t'])
                s = ""
                for t in tmp:
                    L2 = len([x for x in t if x == '\t'])
                    if L1 <= L2:
                        s += t[L1:].rstrip('\t\n') + '\n'
                    else:
                        s += t
                self.nodeDesc = s.rstrip('\t\n') + '\n'
        else:
            self.nodeDesc = ""
        self.setOpen(True)
    
    def text(self, column):
        return self.nodeName

class Model(QHBox):
    def __init__(self, *args):
        QHBox.__init__(self, *args)
        vb = QVBox(self)
        self.list = QListView(vb)
        list = self.list
        list.setRootIsDecorated(True)
        list.addColumn("System Model")
        list.setSorting(-1)
        self.connect(list, SIGNAL("selectionChanged()"), self._change)
        hb = QHButtonGroup(vb)
        self.bt_group = QPushButton("Group", hb)
        self.connect(self.bt_group, SIGNAL("clicked()"), self._add_group)
        self.bt_class = QPushButton("Class", hb)
        self.connect(self.bt_class, SIGNAL("clicked()"), self._add_class)
        self.bt_method = QPushButton("Method", hb)
        self.connect(self.bt_method, SIGNAL("clicked()"), self._add_method)
        self.clear()
        self.editor = edit.NodeEdit(self)
    
    def _change(self):
        item = self.list.selectedItem()
        if item is not None:
            self.editor.use_node(item)
    
    def _add_group(self):
        Node(self.list_top, Node.GROUP, "(new_group)")
    
    def _add_class(self):
        item = self.list.selectedItem()
        if item == None:
            return
        if item.parent() != self.list_top:
            return
        Node(item, Node.CLASS, "(new_class)")
    
    def _add_method(self):
        item = self.list.selectedItem()
        if item == None:
            return
        if (item.parent() is None) or (item.parent().parent() != self.list_top):
            return
        Node(item, Node.METHOD, "(new_method)")
    
    def clear(self):
        self.list.clear()
        self.list_top = Node(self.list, Node.MODEL, "Model")
    
    def load(self, model_file):
        self.clear()
        doc = mdom.parse(model_file)
        if doc.documentElement.tagName != "comarModel":
            raise Exception("not a comar file")
        for group in doc.getElementsByTagName("group"):
            groupItem = Node(self.list_top, Node.GROUP, group.getAttribute("name"), group)
            for class_ in group.getElementsByTagName("class"):
                classItem = Node(groupItem, Node.CLASS, class_.getAttribute("name"), class_)
                for method in class_.getElementsByTagName("method"):
                    Node(classItem, Node.METHOD, method.getAttribute("name"), method)
        doc.unlink()
    
    def save(self, model_file):
        impl = mdom.getDOMImplementation()
        doc = impl.createDocument(None, "comarModel", None)
        g = self.list_top.firstChild()
        while g:
            ge = doc.createElement("group")
            ge.setAttribute("name", g.nodeName)
            doc.documentElement.appendChild(ge)
            c = g.firstChild()
            while c:
                ce = doc.createElement("class")
                ce.setAttribute("name", c.nodeName)
                ge.appendChild(ce)
                m = c.firstChild()
                while m:
                    me = doc.createElement("method")
                    me.setAttribute("name", m.nodeName)
                    if m.nodeDesc:
                        n1 = doc.createTextNode(m.nodeDesc)
                        n2 = doc.createElement("description")
                        me.appendChild(n2)
                        n2.appendChild(n1)
                    ce.appendChild(me)
                    m = m.nextSibling()
                c = c.nextSibling()
            g = g.nextSibling()
        f = codecs.open(model_file, 'w', "utf-8")
        f.write(doc.toprettyxml())
        f.close()
