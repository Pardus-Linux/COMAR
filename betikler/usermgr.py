# -*- coding: utf-8 -*-
#
# Copyright (C) 2006, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#

from string import ascii_letters

# parameters
uid_minimum = 1000
uid_maximum = 65000

# utility functions


class PasswdUser:
    def __init__(self, name, uid, gid, realname, homedir, shell):
        self.name = name
        self.uid = uid
        self.gid = gid
        self.realname = realname
        self.homedir = homedir
        self.shell = shell


class Passwd:
    def __init__(self):
        self.users = {}
        for line in file("/etc/passwd"):
            if line != "" and line != "\n":
                parts = line.rstrip("\n").split(":")
                pu = PasswdUser(parts[0], int(parts[2]), int(parts[3]), parts[4], parts[5], parts[6])
                self.users[pu.uid] = pu
    
    def isNameValid(self, name):
        valid = ascii_letters + "_"
        return len(filter(lambda x: not x in ascii_letters, name)) == 0
    
    def isRealNameValid(self, realname):
        return len(filter(lambda x: x == "\n" or x == ":", realname)) == 0
    
    def set(self, name, uid, gid, realname, homedir, shell):
        if uid == "auto":
            uid = self.next_id()
        pu = PasswdUser(name, uid, gid, realname, homedir, shell)
        self.users[uid] = pu
    
    def next_id(self):
        for i in range(uid_minimum, uid_maximum):
            if not self.users.has_key(i):
                return i
    
    def save(self):
        lines = []
        for uid in self.users.keys():
            pu = self.users[uid]
            lines.append("%s:x:%d:%d:%s:%s:%s\n" % (pu.name, uid, pu.gid, pu.realname, pu.homedir, pu.shell))
        f = file("/etc/passwd", "w")
        f.writelines(lines)
        f.close()


class Shadow:
    def __init__(self):
        self.users = {}
        for line in file("/etc/shadow"):
            if line != "" and line != "\n":
                parts = line.rstrip("\n").split(":")
                # FIXME: huhu


class Group:
    def __init__(self):
        self.groups = {}
        for line in file("/etc/group"):
            if line != "" and line != "\n":
                parts = line.rstrip("\n").split(":")
                # FIXME: huhu


# methods

def userList():
    pass

def setUser(uid, gid, name, realname, homedir, shell):
    pass

def setUserPassword(uid, password):
    pass

def setUserGroups(uid, groups):
    pass

def deleteUser(uid):
    lines = file("/etc/passwd")


def groupList():
    pass

def setGroup(gid, name):
    pass

def deleteGroup(gid):
    pass
