#
# Copyright (C) 2007, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

from qt import *
from kdecore import *
from kdeui import *


class nameWidget(QLineEdit):
    def __init__(self, parent, mode):
        QLineEdit.__init__(self, parent)
        self.mode = mode
        if mode == "edit":
            self.setEnabled(False)
    
    def importValue(self, value):
        self.setText(unicode(value))
    
    def exportValue(self):
        return str(self.text())


class labelWidget(QLineEdit):
    def __init__(self, parent, mode):
        QLineEdit.__init__(self, parent)
        self.mode = mode
    
    def importValue(self, value):
        self.setText(unicode(value))
    
    def exportValue(self):
        return str(self.text())


class passwordWidget(QLineEdit):
    def __init__(self, parent, mode):
        QLineEdit.__init__(self, parent)
        self.mode = mode
    
    def importValue(self, value):
        self.value = value
        self.setText("*" * 10)
        self.clearModified()
    
    def exportValue(self):
        if self.isModified():
            self.value = str(self.text())
        return self.value


class numberWidget(QSpinBox):
    def __init__(self, parent, mode):
        QLineEdit.__init__(self, parent)
        self.setMaxValue(2**16)
        self.setMinValue(0)
        self.mode = mode
    
    def importValue(self, value):
        self.setValue(int(value))
    
    def exportValue(self):
        return self.value()
