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

import ldap

from utility import *
import domain

import browser


class MainWindow(KMainWindow):
    def __init__(self, app):
        KMainWindow.__init__(self)
        self.setAutoSaveSettings()
        self.setMinimumSize(560, 440)
        self.application = app
        
        mbar = self.menuBar()
        menu = QPopupMenu(self)
        mbar.insertItem("&Lider", menu)
        menu.insertItem(i18n("&Quit"), self.slotQuit, Qt.CTRL + Qt.Key_Q)
        
        self.status = QStatusBar(self)
        
        splitter = QSplitter(self)
        splitter.setChildrenCollapsible(False)
        
        self.importDomainConfig()
        
        self.browser = browser.Browser(splitter, self)
        self.browser.setMinimumSize(150, 100)
        
        self.tab = QTabWidget(splitter)
        self.tab.setMinimumSize(150, 100)
        
        self.computers = browser.ObjectList(self.tab, self, "computer")
        self.tab.addTab(self.computers, i18n("Computers"))
        
        self.units = browser.ObjectList(self.tab, self, "unit")
        self.tab.addTab(self.units, i18n("Units"))
        
        self.users = browser.ObjectList(self.tab, self, "user")
        self.tab.addTab(self.users, i18n("Users"))
        
        self.groups = browser.ObjectList(self.tab, self, "group")
        self.tab.addTab(self.groups, i18n("Groups"))
        
        splitter.setSizes([200, 400])
        
        self.setCentralWidget(splitter)
        self.show()
        
        if not len(self.dc.connections):
            self.slotNewDomain()
    
    def showCriticalError(self, message):
        QMessageBox.critical(self, i18n("Critical Error"), message)

    def showWarning(self, message):
        QMessageBox.warning(self, i18n("Warning"), message)

    def showError(self, message):
        QMessageBox.warning(self, i18n("Error"), i18n("Unable to complete operation:") + "\n" + message)

    def showInfo(self, message):
        QMessageBox.information(self, i18n("Information"), message)
    
    def confirm(self, title, message):
        confirm = QMessageBox.question(self, title, message, QMessageBox.Yes, QMessageBox.No)
        if confirm == QMessageBox.Yes:
            return True
        return False
    
    def doubleConfirm(self, title, message1, message2):
        confirm1 = QMessageBox.question(self, title, message1, QMessageBox.Yes, QMessageBox.No)
        if confirm1 == QMessageBox.Yes:
            confirm2 = QMessageBox.question(self, title, message2, QMessageBox.Yes, QMessageBox.No)
            if confirm2 == QMessageBox.Yes:
                return True
        return False
    
    def importDomainConfig(self):
        self.dc = domain.DomainConfig()
        try:
            self.dc.fromXML()
        except domain.DomainXMLParseError, e:
            self.showCriticalError(e.args[0])
    
    def closeEvent(self, e):
        self.slotQuit()
        e.accept()
    
    def slotQuit(self):
        self.dc.toXML()
        self.close()
