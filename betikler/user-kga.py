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
        but = QToolButton(QIconSet(QPixmap("/usr/share/icons/Tulliana-2.0/32x32/actions/add.png")),
            "Add", "lala", self.slotAdd, bar)
        but.setUsesTextLabel(True)
        but.setTextPosition(but.BesideIcon)
        bar.addSeparator()
        but = QToolButton(QIconSet(QPixmap("/usr/share/icons/Tulliana-2.0/32x32/actions/configure.png")),
            "Edit", "lala", self.slotEdit, bar)
        but.setUsesTextLabel(True)
        but.setTextPosition(but.BesideIcon)
        bar.addSeparator()
        but = QToolButton(QIconSet(QPixmap("/usr/share/icons/Tulliana-2.0/32x32/actions/remove.png")),
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
        
        tab.addTab(self.users, QIconSet(QPixmap("/usr/share/icons/Tulliana-2.0/16x16/apps/personal.png")), "Users")
        tab.addTab(self.groups, QIconSet(QPixmap("/usr/share/icons/Tulliana-2.0/16x16/apps/kuser.png")), "Groups")
        
        self.link = link
        link.call("User.Manager.userList", id=1)
        link.call("User.Manager.groupList", id=2)
        self.notifier = QSocketNotifier(link.sock.fileno(), QSocketNotifier.Read)
        self.connect(self.notifier, SIGNAL("activated(int)"), self.slotComar)
    
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
    
    def slotComar(self, sock):
        reply = self.link.read_cmd()
        if reply[0] != self.link.RESULT:
            return
        if reply[1] == 1:
            for user in unicode(reply[2]).split("\n"):
                item = UserItem(self.users, user)
                if item.uid < 1000 or item.uid > 65000:
                    item.setVisible(False)
        elif reply[1] == 2:
            for group in unicode(reply[2]).split("\n"):
                item = GroupItem(self.groups, group)


class UserStack(QVBox):
    def __init__(self, window, parent, link):
        QVBox.__init__(self, parent)


class UserManager(QWidgetStack):
    def __init__(self, window, parent, link):
        QWidgetStack.__init__(self, parent)
        self.browse = BrowseStack(window, self, link)
        self.user = UserStack(window, self, link)




#

link = comar.Link()


app = QApplication([])
app.connect(app, SIGNAL("lastWindowClosed()"), app, SLOT("quit()"))
w = QMainWindow()
w.setMinimumSize(540, 300)
a = UserManager(w, w, link)
w.setCentralWidget(a)
w.show()
app.exec_loop()
