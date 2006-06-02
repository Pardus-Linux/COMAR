#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#

import comar
from qt import *

def getIconSet(name):
    return QIconSet(QPixmap("/usr/share/icons/Tulliana-2.0/" + name))


class UserItem(QListViewItem):
    def __init__(self, parent, line):
        QListViewItem.__init__(self, parent)
        self.uid, self.nick, self.name = line.split("\t")
        self.uid = int(self.uid)
    
    def text(self, col):
        return (str(self.uid), self.nick, self.name)[col]
    
    def compare(self, item, col, ascend):
        if col == 0:
            if self.uid < item.uid:
                return -1
            elif self.uid == item.uid:
                return 0
            else:
                return 1
        else:
            return QListViewItem.compare(self, item, col, ascend)


class GroupItem(QListViewItem):
    def __init__(self, parent, line):
        QListViewItem.__init__(self, parent)
        self.gid, self.name = line.split("\t")
        self.gid = int(self.gid)
    
    def text(self, col):
        return (str(self.gid), self.name)[col]
    
    def compare(self, item, col, ascend):
        if col == 0:
            if self.gid < item.gid:
                return -1
            elif self.gid == item.gid:
                return 0
            else:
                return 1
        else:
            return QListViewItem.compare(self, item, col, ascend)


class BrowseStack(QVBox):
    def __init__(self, window, parent, link):
        QWidget.__init__(self, parent)
        self.setMargin(6)
        self.setSpacing(6)
        
        bar = QToolBar("lala", window, self)
        but = QToolButton(getIconSet("32x32/actions/add.png"),
            "Add", "lala", self.slotAdd, bar)
        but.setUsesTextLabel(True)
        but.setTextPosition(but.BesideIcon)
        bar.addSeparator()
        but = QToolButton(getIconSet("32x32/actions/configure.png"),
            "Edit", "lala", self.slotEdit, bar)
        but.setUsesTextLabel(True)
        but.setTextPosition(but.BesideIcon)
        bar.addSeparator()
        but = QToolButton(getIconSet("32x32/actions/remove.png"),
            "Delete", "lala", self.slotDelete, bar)
        but.setUsesTextLabel(True)
        but.setTextPosition(but.BesideIcon)
        
        lab = QLabel("", bar)
        bar.setStretchableWidget(lab)
        
        toggle = QRadioButton("Show system user and groups", bar)
        self.connect(toggle, SIGNAL("toggled(bool)"), self.slotToggle)
        
        tab = QTabWidget(self)
        tab.setMargin(6)
        
        self.users = QListView(tab)
        self.users.addColumn("ID")
        self.users.setColumnAlignment(0, Qt.AlignRight)
        self.users.addColumn("User name")
        self.users.setColumnAlignment(1, Qt.AlignHCenter)
        self.users.addColumn("Real name")
        
        self.groups = QListView(tab)
        self.groups.addColumn("ID")
        self.groups.setColumnAlignment(0, Qt.AlignRight)
        self.groups.addColumn("Name")
        
        tab.addTab(self.users, getIconSet("16x16/apps/personal.png"), "Users")
        tab.addTab(self.groups, getIconSet("16x16/apps/kuser.png"), "Groups")
        
        self.link = link
        link.call("User.Manager.userList", id=1)
        link.call("User.Manager.groupList", id=2)
    
    def slotAdd(self):
        pass
    
    def slotEdit(self):
        pass
    
    def slotDelete(self):
        pass
    
    def slotToggle(self, on):
        item = self.users.firstChild()
        while item:
            if item.uid < 1000 or item.uid > 65000:
                item.setVisible(on)
            item = item.nextSibling()
    
    def comarUsers(self, reply):
        if reply[0] != self.link.RESULT:
            return
        for user in unicode(reply[2]).split("\n"):
            item = UserItem(self.users, user)
            if item.uid < 1000 or item.uid > 65000:
                item.setVisible(False)
    
    def comarGroups(self, reply):
        if reply[0] != self.link.RESULT:
            return
        for group in unicode(reply[2]).split("\n"):
            item = GroupItem(self.groups, group)


class PathEntry(QHBox):
    def __init__(self, parent, question, is_dir=True):
        QHBox.__init__(self, parent)
        self.is_dir = is_dir
        self.question = question
        self.setSpacing(3)
        self.path = QLineEdit(self)
        self.path.setMinimumWidth(160)
        but = QPushButton("...", self)
        self.connect(but, SIGNAL("clicked()"), self.browse)

    def browse(self):
        if self.is_dir:
            s = QFileDialog.getExistingDirectory(self.path.text(), self, "lala", self.question, False)
        else:
            s = QFileDialog.getOpenFileName(self.path.text(), "All (*)", self, "lala", self.question)
        self.path.setText(s)

    def text(self):
        return str(self.path.text())

    def setText(self, text):
        self.path.setText(text)


class UserStack(QVBox):
    def __init__(self, window, parent, link):
        QVBox.__init__(self, parent)
        self.setMargin(6)
        self.setSpacing(6)
        
        hb = QHBox(self)
        hb.setSpacing(6)
        
        w = QWidget(hb)
        grid = QGridLayout(w)
        grid.setSpacing(6)
        
        lab = QLabel("ID:", w)
        hb2 = QHBox(w)
        hb2.setSpacing(6)
        self.w_id = QLineEdit(hb2)
        self.w_id_auto = QRadioButton("Automatic", hb2)
        grid.addWidget(lab, 0, 0, Qt.AlignRight)
        grid.addWidget(hb2, 0, 1)
        
        lab = QLabel("Name:", w)
        self.w_nick = QLineEdit(w)
        grid.addWidget(lab, 1, 0, Qt.AlignRight)
        grid.addWidget(self.w_nick, 1, 1)
        
        lab = QLabel("Real name:", w)
        self.w_name = QLineEdit(w)
        grid.addWidget(lab, 2, 0, Qt.AlignRight)
        grid.addWidget(self.w_name, 2, 1)
        
        lab = QLabel("Main group:", w)
        grid.addWidget(lab, 3, 0, Qt.AlignRight)
        
        lab = QLabel("Home:", w)
        self.w_home = PathEntry(w, "Select home directory for user")
        grid.addWidget(lab, 4, 0, Qt.AlignRight)
        grid.addWidget(self.w_home, 4, 1)
        
        self.w_home_create = QRadioButton("Create directory", w)
        grid.addWidget(self.w_home_create, 5, 1)
        
        lab = QLabel("Shell:", w)
        self.w_shell = QComboBox(True, w)
        self.w_shell.insertItem("/bin/bash", 0)
        self.w_shell.insertItem("/bin/false", 1)
        grid.addWidget(lab, 6, 0, Qt.AlignRight)
        grid.addWidget(self.w_shell, 6, 1)
        
        lab = QLabel("Password:", w)
        self.w_pass = QLineEdit(w)
        self.w_pass.setEchoMode(self.w_pass.Password)
        grid.addWidget(lab, 7, 0, Qt.AlignRight)
        grid.addWidget(self.w_pass, 7, 1)
        
        lab = QLabel("Confirm password:", w)
        self.w_pass2 = QLineEdit(w)
        self.w_pass2.setEchoMode(self.w_pass2.Password)
        grid.addWidget(lab, 8, 0, Qt.AlignRight)
        grid.addWidget(self.w_pass2, 8, 1)
        
        lab = QLabel(" ", w)
        grid.addWidget(lab, 9, 1)
        
        w = QWidget(hb)
        vb = QVBoxLayout(w)
        but = QRadioButton("Show all groups", w)
        vb.addWidget(but, 0, Qt.AlignRight)
        self.groups = QListView(w)
        vb.addWidget(self.groups)
        
        hb = QHBox(self)
        hb.setSpacing(12)
        QLabel(" ", hb)
        QPushButton(getIconSet("16x16/actions/add.png"), "Add", hb)
        QPushButton(getIconSet("16x16/actions/cancel.png"), "Cancel", hb)


class UserManager(QWidgetStack):
    def __init__(self, window, parent):
        link = comar.Link()
        self.link = link
        self.notifier = QSocketNotifier(link.sock.fileno(), QSocketNotifier.Read)
        self.connect(self.notifier, SIGNAL("activated(int)"), self.slotComar)
        
        QWidgetStack.__init__(self, parent)
        #self.browse = BrowseStack(window, self, link)
        self.user = UserStack(window, self, link)
    
    def slotComar(self, sock):
        reply = self.link.read_cmd()
        if reply[1] == 1:
            self.browse.comarUsers(reply)
        elif reply[1] == 2:
            self.browse.comarGroups(reply)




#


app = QApplication([])
app.connect(app, SIGNAL("lastWindowClosed()"), app, SLOT("quit()"))
w = QMainWindow()
w.setMinimumSize(540, 300)
a = UserManager(w, w)
w.setCentralWidget(a)
w.show()
app.exec_loop()
