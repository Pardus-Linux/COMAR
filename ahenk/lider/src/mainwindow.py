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
        pass
    
    def slotAddDomainComponent(self):
        item = self.browser.selectedItem()
        if not item:
            return
        
        item.insertDC("com")
