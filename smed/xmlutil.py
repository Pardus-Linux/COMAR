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

import xml.dom.minidom as mdom

def newDocument(rootTag):
    impl = mdom.getDOMImplementation()
    doc = impl.createDocument(None, rootTag, None)
    return doc

def addNode(doc, parent, tag):
    if parent == doc:
        parent = doc.documentElement
    child = doc.createElement(tag)
    parent.appendChild(child)
    return child

def addText(doc, parent, text):
    cdata =doc.createTextNode(text)
    parent.appendChild(cdata)

def addTextNode(doc, parent, tag, text):
    child = addNode(doc, parent, tag)
    cdata = doc.createTextNode(text)
    child.appendChild(cdata)

def parseDocument(fileName, rootTag):
    doc = mdom.parse(fileName)
    if doc.documentElement.tagName != rootTag:
        raise Exception("not a comar file")
    return doc

def getTagsByName(parent, childName):
    return [x for x in parent.childNodes if x.nodeType == x.ELEMENT_NODE if x.tagName == childName]

def getNodeText(node, tag, default=None):
    try:
        c = getTagByName(node, tag)[0].firstChild.data
    except:
        c = default
    return c
