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

def isNameValid(name):
    valid = ascii_letters + "_"
    return len(filter(lambda x: not x in ascii_letters, name)) == 0

def isRealNameValid(realname):
    return len(filter(lambda x: x == "\n" or x == ":", realname)) == 0


class User:
    pass


class Group:
    pass


class Database:
    passwd_path = "/etc/passwd"
    shadow_path = "/etc/shadow"
    group_path = "/etc/group"
    
    def __init__(self):
        self.users = {}
        self.users_by_name = {}
        self.groups = {}
        
        # FIXME: lock files
        
        for line in file(self.passwd_path):
            if line != "" and line != "\n":
                parts = line.rstrip("\n").split(":")
                user = User()
                user.name = parts[0]
                user.uid = int(parts[2])
                user.gid = int(parts[3])
                user.realname = parts[4]
                user.homedir = parts[5]
                user.shell = parts[6]
                self.users[user.uid] = user
                self.users_by_name[user.name] = user
        
        for line in file(self.shadow_path):
            if line != "" and line != "\n":
                parts = line.rstrip("\n").split(":")
                user = self.users_by_name[parts[0]]
                user.password = parts[1]
                user.pwrest = parts[2:]
        
        for line in file(self.group_path):
            if line != "" and line != "\n":
                parts = line.rstrip("\n").split(":")
                group = Group()
                group.name = parts[0]
                group.gid = parts[2]
                group.members = parts[3].split(",")
        
        # FIXME: unlock files
    
    def sync(self):
        # FIXME: lock files
        
        lines = []
        for uid in self.users.keys():
            pu = self.users[uid]
            lines.append("%s:x:%d:%d:%s:%s:%s\n" % (pu.name, uid, pu.gid, pu.realname, pu.homedir, pu.shell))
        f = file(self.passwd_path, "w")
        f.writelines(lines)
        f.close()
        
        lines = []
        for su in self.users.keys():
            lines.append("%s:%s:%s\n" % (su.name, su.password, ":".join(su.pwrest)))
        f = file(self.shadow_path, "w")
        f.writelines(lines)
        f.close()
        
        lines = []
        for gid in self.groups.keys():
            group = self.groups[gid]
            lines.append("%s:x:%s:%s\n" % (group.name, gid, ",".join(group.members)))
        f = file(self.group_path, "w")
        f.writelines(lines)
        f.close()
        
        # FIXME: unlock files
    
    def next_uid(self):
        for i in range(uid_minimum, uid_maximum):
            if not self.users.has_key(i):
                return i


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
    pass

def groupList():
    pass

def setGroup(gid, name):
    pass

def deleteGroup(gid):
    pass
