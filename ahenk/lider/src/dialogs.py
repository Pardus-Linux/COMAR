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

import domain
from utility import *


class DomainDialog(KDialog):
    """Domain connection dialog."""
    
    def __init__(self, parent, connection=None):
        KDialog.__init__(self, parent)
        self.connection = connection
        
        if connection:
            self.setCaption(i18n("%1 Properties").arg(connection.label))
        else:
            self.setCaption(i18n("Add New Domain"))
        
        self.resize(420, 170)
        
        vb = QVBoxLayout(self, 6)
        vb.setMargin(12)
        
        grid = QGridLayout(1, 2, 6)
        vb.addLayout(grid)
        
        lab = QLabel(i18n("Label:"), self)
        grid.addWidget(lab, 0, 0, Qt.AlignRight)
        self.w_name = QLineEdit(self)
        grid.addWidget(self.w_name, 0, 1)
        
        lab = QLabel(i18n("Directory server:"), self)
        grid.addWidget(lab, 1, 0, Qt.AlignRight)
        self.w_host = QLineEdit(self)
        grid.addWidget(self.w_host, 1, 1)
        
        lab = QLabel(i18n("Base DN:"), self)
        grid.addWidget(lab, 2, 0, Qt.AlignRight)
        self.w_base_dn = QLineEdit(self)
        grid.addWidget(self.w_base_dn, 2, 1)
        
        lab = QLabel(i18n("Bind DN:"), self)
        grid.addWidget(lab, 3, 0, Qt.AlignRight)
        self.w_bind_dn = QLineEdit(self)
        grid.addWidget(self.w_bind_dn, 3, 1)
        
        lab = QLabel(i18n("Bind Password:"), self)
        grid.addWidget(lab, 4, 0, Qt.AlignRight)
        self.w_bind_pass = QLineEdit(self)
        grid.addWidget(self.w_bind_pass, 4, 1)
        
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
        
        if connection:
            self.useValues(connection)
    
    def isModified(self):
        return self.w_name.isModified()
    
    def useValues(self, connection):
        self.w_name.setText(unicode(connection.label))
        self.w_host.setText(connection.host)
        self.w_base_dn.setText(connection.base_dn)
        self.w_bind_dn.setText(connection.bind_dn)
        self.w_bind_pass.setText(connection.bind_password)
    
    def setValues(self):
        if self.connection:
            self.connection.label = unicode(self.w_name.text())
            self.connection.host = unicode(self.w_host.text())
            self.connection.base_dn = unicode(self.w_base_dn.text())
            self.connection.bind_dn = unicode(self.w_bind_dn.text())
            self.connection.bind_password = unicode(self.w_bind_pass.text())
        else:
            self.connection = domain.Connection(unicode(self.w_name.text()),
                                                unicode(self.w_host.text()),
                                                unicode(self.w_base_dn.text()),
                                                unicode(self.w_bind_dn.text()),
                                                unicode(self.w_bind_pass.text()))
    
    def accept(self):
        self.setValues()
        KDialog.accept(self)
    
    def reject(self):
        KDialog.reject(self)


class DirectoryDialog(KDialog):
    """Directory attributes dialog."""
    
    def __init__(self, parent, dn, dc="", o=""):
        KDialog.__init__(self, parent)
        self.dn = dn
        self.dc = dc
        self.o = o
        
        if dc:
            self.setCaption(i18n("%1 Properties").arg(dc))
        else:
            self.setCaption(i18n("New Directory"))
        
        self.resize(320, 120)
        
        vb = QVBoxLayout(self, 6)
        vb.setMargin(12)
        
        grid = QGridLayout(1, 2, 6)
        vb.addLayout(grid)
        
        lab = QLabel(i18n("DN:"), self)
        grid.addWidget(lab, 0, 0, Qt.AlignRight)
        self.w_dn = QLineEdit(self)
        self.w_dn.setEnabled(False)
        grid.addWidget(self.w_dn, 0, 1)
        
        lab = QLabel(i18n("Name:"), self)
        grid.addWidget(lab, 1, 0, Qt.AlignRight)
        self.w_dc = QLineEdit(self)
        grid.addWidget(self.w_dc, 1, 1)
        
        lab = QLabel(i18n("Label:"), self)
        grid.addWidget(lab, 2, 0, Qt.AlignRight)
        self.w_o = QLineEdit(self)
        grid.addWidget(self.w_o, 2, 1)
        
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
        
        if dc:
            self.w_dc.setEnabled(False)
        self.useValues(dn, dc, o)
    
    def isModified(self):
        return self.w_dc.isModified()
    
    def useValues(self, dn, dc, o):
        self.w_dn.setText(dn)
        self.w_dc.setText(dc)
        self.w_o.setText(unicode(o))
    
    def setValues(self):
        self.dn = self.w_dn.text()
        self.dc = self.w_dc.text()
        self.o = unicode(self.w_o.text())
    
    def accept(self):
        self.setValues()
        KDialog.accept(self)
    
    def reject(self):
        KDialog.reject(self)


class ComputerDialog(KDialog):
    """Computer attributes dialog."""
    
    def __init__(self, parent, dn, model=None):
        KDialog.__init__(self, parent)
        self.dn = dn
        self.model = model
        
        if model:
            self.setCaption(i18n("%1 Properties").arg(model.name))
        else:
            self.setCaption(i18n("New Computer"))
        
        self.resize(320, 120)
        
        vb = QVBoxLayout(self, 6)
        vb.setMargin(12)
        
        grid = QGridLayout(1, 2, 6)
        vb.addLayout(grid)
        
        # DN
        lab = QLabel(i18n("DN:"), self)
        if not self.model:
            lab.setText(i18n("Parent DN:"))
        grid.addWidget(lab, 0, 0, Qt.AlignRight)
        self.w_dn = QLineEdit(self)
        self.w_dn.setEnabled(False)
        grid.addWidget(self.w_dn, 0, 1)
        
        # CN
        lab = QLabel(i18n("Name:"), self)
        grid.addWidget(lab, 1, 0, Qt.AlignRight)
        self.w_cn = QLineEdit(self)
        grid.addWidget(self.w_cn, 1, 1)
        
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
        
        self.useValues(dn, model)
    
    def isModified(self):
        return self.w_cn.isModified()
    
    def useValues(self, dn, model):
        self.w_dn.setText(dn)
        if model and dn.startswith("cn"):
            self.w_cn.setText(model.name)
    
    def setValues(self):
        self.dn = str(self.w_dn.text())
        if not self.model:
            self.model = domain.ComputerModel()
            self.model.type.append("pardusComputer")
            self.model.type.append("device")
            self.model.type.append("top")
        self.model.name = str(self.w_cn.text())
    
    def accept(self):
        self.setValues()
        KDialog.accept(self)
    
    def reject(self):
        KDialog.reject(self)
