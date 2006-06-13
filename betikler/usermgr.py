# -*- coding: utf-8 -*-
#
# Copyright (C) 2006, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#

import os
from string import ascii_letters
import time
import fcntl
import md5
import random

# parameters
uid_minimum = 1000
uid_maximum = 65000

# utility functions


class FileLock:
    def __init__(self, filename):
        self.filename = filename
        self.fd = None
    
    def lock(self, shared=False, timeout=0):
        type = fcntl.LOCK_EX
        if shared:
            type = fcntl.LOCK_SH
        self.fd = os.open(self.filename, os.O_WRONLY | os.O_CREAT, 0600)
        if self.fd == -1:
            raise "Cannot create lock file"
        while True:
            try:
                fcntl.flock(self.fd, type | fcntl.LOCK_NB)
                return
            except IOError:
                if timeout > 0:
                    time.sleep(0.2)
                    timeout -= 0.2
                else:
                    os.close(self.fd)
                    raise
    
    def unlock(self):
        os.close(self.fd)


#

def checkName(name):
    valid = ascii_letters + "_"
    if len(filter(lambda x: not x in valid, name)) != 0:
        fail("User name is invalid")

def checkRealName(realname):
    if len(filter(lambda x: x == "\n" or x == ":", realname)) != 0:
        fail("Real name is invalid")

#

class User:
    def __init__(self):
        self.password = None
    
    def __str__(self):
        return "%s (%d, %d)\n  %s\n  %s\n  %s\n  %s" % (
            self.name, self.uid, self.gid,
            self.realname, self.homedir, self.shell,
            self.password
        )


class Group:
    def __str__(self):
        str = "%s (%d)" % (self.name, self.gid)
        for name in self.members:
            str += "\n %s" % name
        return str


class Database:
    passwd_path = "/etc/passwd"
    shadow_path = "/etc/shadow"
    group_path = "/etc/group"
    lock_path = "/etc/.pwd.lock"
    
    def __init__(self, for_read=False):
        self.lock = FileLock(self.lock_path)
        self.lock.lock(shared=for_read)
        
        self.users = {}
        self.users_by_name = {}
        self.groups = {}
        
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
                if self.users_by_name.has_key(parts[0]):
                    user = self.users_by_name[parts[0]]
                    user.password = parts[1]
                    user.pwrest = parts[2:]
        
        for line in file(self.group_path):
            if line != "" and line != "\n":
                parts = line.rstrip("\n").split(":")
                group = Group()
                group.name = parts[0]
                group.gid = int(parts[2])
                group.members = parts[3].split(",")
                self.groups[group.gid] = group
    
    def sync(self):
        lines = []
        keys = self.users.keys()
        keys.sort()
        for uid in keys:
            user = self.users[uid]
            lines.append("%s:x:%d:%d:%s:%s:%s\n" % (
                user.name, uid, user.gid,
                user.realname, user.homedir, user.shell
            ))
        f = file(self.passwd_path, "w")
        f.writelines(lines)
        f.close()
        
        lines = []
        keys = self.users.keys()
        keys.sort()
        for uid in keys:
            user = self.users[uid]
            if user.password:
                lines.append("%s:%s:%s\n" % (
                    user.name,
                    user.password,
                    ":".join(user.pwrest)
                ))
        f = file(self.shadow_path, "w")
        f.writelines(lines)
        f.close()
        
        lines = []
        keys = self.groups.keys()
        keys.sort()
        for gid in keys:
            group = self.groups[gid]
            lines.append("%s:x:%s:%s\n" % (group.name, gid, ",".join(group.members)))
        f = file(self.group_path, "w")
        f.writelines(lines)
        f.close()
    
    def next_uid(self):
        for i in range(uid_minimum, uid_maximum):
            if not self.users.has_key(i):
                return i


# methods

def userList():
    def format(dict, uid):
        item = dict[uid]
        return "%s\t%s\t%s" % (item.uid, item.name, item.realname)
    db = Database(for_read=True)
    ret = "\n".join(map(lambda x: format(db.users, x), db.users))
    return ret

def userInfo(uid):
    pass

def addUser(uid, gid, name, realname, homedir, shell, password, groups):
    checkName(name)
    checkRealName(realname)
    
    db = Database()
    if uid == "auto":
        uid = db.next_uid()
    else:
        uid = int(uid)
        if db.users.has_key(uid):
            fail("This user ID is already used")
    u = User()
    u.uid = uid
    u.gid = gid
    u.name = name
    u.realname = realname
    u.homedir = homedir
    u.shell = shell
    u.password = shadowCrypt(password)
    u.pwrest = [ "13094", "0", "99999", "7", "", "", "" ]
    db.users[uid] = u
    db.sync()

def setUser(uid, realname, homedir, shell, password, groups):
    pass

def deleteUser(uid):
    uid = int(uid)
    if uid == 0:
        fail("You cant delete root user")
    
    db = Database()
    if db.users.has_key(uid):
        db.users[uid] = None
        db.sync()

def groupList():
    import piksemel
    gdefs = {}
    doc = piksemel.parse("/etc/comar/security-comments.xml")
    for item in doc.getTag("groups").tags():
        gdefs[item.getAttribute("name")] = (
            item.getTagData("purpose"),
            item.getTagData("comment")
        )
    def format(defs, dict, gid):
        item = dict[gid]
        if defs.has_key(item.name):
            d = defs[item.name]
            return "%s\t%s\t%s\t%s" % (item.gid, item.name, d[0], d[1])
        else:
            return "%s\t%s" % (item.gid, item.name)
    db = Database(for_read=True)
    ret = "\n".join(map(lambda x: format(gdefs, db.groups, x), db.groups))
    return ret

def addGroup(gid, name):
    checkName(name)
    
    db = Database()
    if gid == "auto":
        pass
    else:
        if db.groups.has_key(gid):
            fail("This group ID is already used")
        gid = int(gid)
    g = Group()
    g.gid = gid
    g.name = name
    g.members = []
    db.groups[gid] = g
    db.sync()

def deleteGroup(gid):
    db = Database()
    gid = int(gid)
    if db.groups.has_key(gid):
        db.groups[gid] = None
    db.sync()


#
# Crypt function for shadow file
#

def shadowCrypt(password):
    des_salt = list('./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
    salt, magic = str(random.random())[-8:], '$1$'
    
    ctx = md5.new(password)
    ctx.update(magic)
    ctx.update(salt)
    
    ctx1 = md5.new(password)
    ctx1.update(salt)
    ctx1.update(password)
    
    final = ctx1.digest()
    
    for i in range(len(password), 0 , -16):
        if i > 16:
            ctx.update(final)
        else:
            ctx.update(final[:i])
    
    i = len(passwd)
    
    while i:
        if i & 1:
            ctx.update('\0')
        else:
            ctx.update(password[:1])
        i = i >> 1
    final = ctx.digest()
    
    for i in range(1000):
        ctx1 = md5.new()
        if i & 1:
            ctx1.update(password)
        else:
            ctx1.update(final)
        if i % 3: ctx1.update(salt)
        if i % 7: ctx1.update(password)
        if i & 1:
            ctx1.update(final)
        else:
            ctx1.update(password)
        final = ctx1.digest()
    
    def _to64(v, n):
        r = ''
        while (n-1 >= 0):
            r = r + des_salt[v & 0x3F]
            v = v >> 6
            n = n - 1
        return r
    
    rv = magic + salt + '$'
    final = map(ord, final)
    l = (final[0] << 16) + (final[6] << 8) + final[12]
    rv = rv + _to64(l, 4)
    l = (final[1] << 16) + (final[7] << 8) + final[13]
    rv = rv + _to64(l, 4)
    l = (final[2] << 16) + (final[8] << 8) + final[14]
    rv = rv + _to64(l, 4)
    l = (final[3] << 16) + (final[9] << 8) + final[15]
    rv = rv + _to64(l, 4)
    l = (final[4] << 16) + (final[10] << 8) + final[5]
    rv = rv + _to64(l, 4)
    l = final[11]
    rv = rv + _to64(l, 2)
    
    return rv
