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
from kdeui import *
from kdecore import *

import ldapview
import ldapmodel
from utility import *


class DomainProperties(KDialog):
    def __init__(self, parent, dom=None):
        KDialog.__init__(self, parent)
        self.dom = dom
        if dom:
            self.setCaption(i18n("%s Properties") % dom.name)
        else:
            self.setCaption(i18n("Add New Domain"))
        self.resize(420, 220)
        
        vb = QVBoxLayout(self, 6)
        vb.setMargin(12)
        
        grid = QGridLayout(1, 2, 6)
        vb.addLayout(grid)
        
        lab = QLabel(i18n("Name:"), self)
        grid.addWidget(lab, 0, 0, Qt.AlignRight)
        self.w_name = QLineEdit(self)
        grid.addWidget(self.w_name, 0, 1)
        
        lab = QLabel(i18n("Directory server:"), self)
        grid.addWidget(lab, 1, 0, Qt.AlignRight)
        self.w_host = QLineEdit(self)
        grid.addWidget(self.w_host, 1, 1)
        
        lab = QLabel(i18n("Bind DN:"), self)
        grid.addWidget(lab, 2, 0, Qt.AlignRight)
        self.w_bind_dn = QLineEdit(self)
        grid.addWidget(self.w_bind_dn, 2, 1)
        
        lab = QLabel(i18n("Bind Password:"), self)
        grid.addWidget(lab, 3, 0, Qt.AlignRight)
        self.w_bind_pass = QLineEdit(self)
        grid.addWidget(self.w_bind_pass, 3, 1)
        
        lay = QHBoxLayout()
        vb.addLayout(lay)
        lay.setMargin(3)
        lay.setSpacing(12)
        
        but = QPushButton(getIconSet("apply", KIcon.Small), i18n("Apply"), self)
        lay.addWidget(but)
        self.connect(but, SIGNAL("clicked()"), self.accept)
        
        but = QPushButton(getIconSet("cancel", KIcon.Small), i18n("Cancel"), self)
        lay.addWidget(but)
        self.connect(but, SIGNAL("clicked()"), self.reject)
        
        if dom:
            self.useValues(dom)
    
    def useValues(self, dom):
        self.w_name.setText(unicode(dom.name))
        self.w_host.setText(dom.host)
        self.w_bind_dn.setText(dom.bind_dn)
        self.w_bind_pass.setText(dom.bind_password)
    
    def setValues(self):
        self.dom.name = unicode(self.w_name.text())
        self.dom.host = unicode(self.w_host.text())
        self.dom.bind_dn = unicode(self.w_bind_dn.text())
        self.dom.bind_password = unicode(self.w_bind_pass.text())
    
    def accept(self):
        if not self.dom:
            self.dom = ldapmodel.Domain()
        self.setValues()
        ldapview.Item(self.parent().browser, self.dom)
        self.parent().browser.save()
        KDialog.accept(self)
    
    def reject(self):
        KDialog.reject(self)


class MainWindow(KMainWindow):
    def __init__(self):
        KMainWindow.__init__(self)
        self.setMinimumSize(560, 440)
        
        self.act_add_domain = QAction(getIconSet("gear"), i18n("Add Domain"), Qt.CTRL + Qt.Key_D, self)
        self.connect(self.act_add_domain, SIGNAL("activated()"), self.slotAddDomain)
        
        self.act_add_dc = QAction(getIconSet("user"), i18n("Add Domain Component"), Qt.CTRL + Qt.Key_C, self)
        self.connect(self.act_add_dc, SIGNAL("activated()"), self.slotAddDomainComponent)
        
        mbar = self.menuBar()
        menu = QPopupMenu(self)
        mbar.insertItem(i18n("&Domain"), menu)
        self.act_add_domain.addTo(menu)
        menu.insertSeparator()
        menu.insertItem(i18n("&Quit"), self.slotQuit, Qt.CTRL + Qt.Key_Q)
        
        bar = QToolBar(self)
        self.act_add_domain.addTo(bar)
        self.act_add_dc.addTo(bar)
        
        self.browser = ldapview.Browser(self)
        self.connect(self.browser, SIGNAL("selectionChanged()"), self.slotBrowserChange)
        self.setCentralWidget(self.browser)
        
        self.slotBrowserChange()
    
    def slotQuit(self):
        KApplication.kApplication().closeAllWindows()
    
    def slotBrowserChange(self):
        dc = False
        item = self.browser.selectedItem()
        if item:
            dc = True
        
        self.act_add_dc.setEnabled(dc)
    
    def slotAddDomain(self):
        win = DomainProperties(self)
        win.show()
    
    def slotAddDomainComponent(self):
        item = self.browser.selectedItem()
        if not item:
            return
        
        item.insertDC("com")
