#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

__version__ = '1.16'


#
# Compatibility with 1.0
# import comar should have Link class
#

import socket
import select
import struct

class Error(Exception):
    """Obsolete class, dont use in new clients"""
    pass

class CannotConnect(Exception):
    """Connection to the comar failed"""
    pass

class LinkClosed(Exception):
    """Connection with comar is closed"""
    pass


class Reply:
    """Representation of comar daemon's message."""
    
    cmdmap = {
        0: "result",
        1: "fail",
        2: "none",
        3: "denied",
        4: "error",
        5: "start",
        6: "end",
        7: "notify"
    }
    
    def __init__(self, cmd, id, data):
        # We keep a copy of data in old style parsed order for old clients
        if cmd == 0:
            tmp = data.split(" ", 1)
            self._obsolete = (cmd, id, tmp[1], tmp[0])
        else:
            self._obsolete = (cmd, id, data)
        
        self.command = self.cmdmap[cmd]
        self.id = id
        self.data = data
        
        # Sender script information is embedded in data for certain replies
        self.script = "comar"
        if self.command in ("result", "none", "fail", "error"):
            if " " in data:
                self.script, self.data = data.split(" ", 1)
        
        # Further parse notification message
        self.notify = None
        if self.command == "notify":
            self.notify, self.script, self.data = data.split("\n", 2)
    
    def __getitem__(self, key):
        # Obsolete access method, use class methods for new clients
        if isinstance(key, int):
            return self._obsolete[key]
        raise IndexError("Index should be an integer")
    
    def __str__(self):
        if self.command == "notify":
            return "notify (%s, %s) = [%s]" % (
                self.script,
                self.notify,
                self.data
            )
        else:
            return "%s (%s, %d) = [%s]" % (
                self.command,
                self.script,
                self.id,
                self.data
            )


class Call:
    def __init__(self, link, group, class_=None, package=None, func=None):
        self.link = link
        self.group = group
        self.class_ = class_
        self.package = package
        self.func = func
    
    def __repr__(self):
        return "Comar Call object %s.%s[%s].%s" % (
            self.group, self.class_, self.package, self.func
        )
    
    def __getitem__(self, key):
        if not self.class_:
            raise KeyError, "Package should be selected after class"
        if not isinstance(key, basestring):
            raise KeyError
        return Call(self.link, self.group, self.class_, key)
    
    def __getattr__(self, name):
        if self.class_:
            c = Call(self.link, self.group, self.class_, self.package, name)
            return c.call
        else:
            if name[0] < 'A' or name[0] > 'Z':
                raise AttributeError
            return Call(self.link, self.group, name)
    
    def call(self, **args):
        method = "%s.%s.%s" % (self.group, self.class_, self.func)
        id = 0
        if args.has_key("id"):
            id = args["id"]
            del args["id"]
        if self.package:
            self.link.call_package(method, self.package, args, id)
        else:
            self.link.call(method, args, id)


class Link:
    """A class for communicating with comar daemon."""
    
    # rpc commands, keep in sync with rpc_unix.c
    RESULT = 0
    FAIL = 1
    NONE = 2
    DENIED = 3
    ERROR = 4
    RESULT_START = 5
    RESULT_END = 6
    NOTIFY = 7
    # following cmds are sent by internal methods, thus not visible to outside
    __LOCALIZE = 8
    __REGISTER = 9
    __REMOVE = 10
    __CALL = 11
    __CALL_PACKAGE = 12
    __ASKNOTIFY = 13
    __GETLIST = 14
    __CHECKACL = 15
    __DUMPPROFILE = 16
    __CANCEL = 17
    
    def __init__(self, sockname="/var/run/comar.socket"):
        try:
            self.sock = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
            self.sock.connect(sockname)
        except socket.error:
            raise CannotConnect('Connection to COMAR socket %s failed' % sockname)
    
    def __getattr__(self, name):
        if name[0] < 'A' or name[0] > 'Z':
            raise AttributeError
        
        return Call(self, name)
    
    def __pack(self, cmd, id, args):
        size = 0
        args2 = []
        # COMAR RPC is using network byte order (big endian)
        fmt = "!ii"
        for a in args:
                    a = str(a)      # for handling unicode
                    fmt += "h%dsB" % (len(a))
                    size += 2 + len(a) + 1
                    args2.append(len(a))
                    args2.append(a.encode("utf-8"))
                    args2.append(0)
        pak = struct.pack(fmt, (cmd << 24) | size, id, *args2)
        return pak
    
    def __recv(self, size):
        data = ""
        while size:
            tmp = self.sock.recv(size, socket.MSG_WAITALL)
            if tmp == "":
                raise LinkClosed("recv failed at %d of %d" % (len(data), size))
            data += tmp
            size -= len(tmp)
        return data
    
    def read(self):
        """Read a reply from comar.
        
        If there isn't any data waiting at connection, this function
        immediately returns None. If there is data, returned value
        is a tuple of three or four items: (command, id, data, package)
        
        Command is a reply code defined at the start of this class.
        ID is the original id value from the request sent to the comard.
        Data is the return value in string format.
        Last item package is only available in RESULT replies and indicates
        which package's script that the reply came from.
        
        Reply code meanings:
        RESULT: Operation successful.
        FAIL: Called script had a problem while trying to perform operation.
        NONE: There isn't any script registered for given class.
        DENIED: You aren't allowed to do that operation.
        ERROR: Comar had a problem while trying to perform operation.
        RESULT_START: Class is implemented by multiple scripts, and their
        result will follow.
        RESULT_END: All of the class' scripts run.
        NOTIFY: You got a notification event.
        """
        
        fds = select.select([self.sock], [], [], 0)
        if fds[0] == []:
            return None
        data = self.__recv(8)
        head = struct.unpack('!ii', str(data))
        cmd = head[0] >> 24
        size = head[0] & 0x00ffffff
        if size:
            data = self.__recv(size)
        else:
            data = None
        
        return Reply(cmd, head[1], data)
    
    def read_cmd(self):
        """Read a reply from comar.
        
        This method behaves like read method, except that it waits until
        a full message comes from the COMAR daemon.
        """
        while 1:
            fds = select.select([self.sock], [], [])
            if fds[0] != []:
                break
        return self.read()
    
    def localize(self, localename=None):
        """Set the language for translated replies.
        
        Since comar has no way to detect caller's locale, this command
        is used for sending user's language to the comard. Afterwards,
        all the jobs started with API calls uses translated messages in
        their replies.
        
        You can get the localename parameter from locale.getlocale call.
        """
        if not localename:
            import locale
            lang = locale.setlocale(locale.LC_MESSAGES)
            if "_" in lang:
                localename = lang.split("_", 1)[0]
            else:
                localename = "en"
        pak = self.__pack(self.__LOCALIZE, 0, [localename])
        self.sock.send(pak)
    
    def register(self, classname, packagename, cslfile, id=0):
        """Register a package script on the system model.
        """
        pak = self.__pack(self.__REGISTER, id,
                                  [ classname, packagename, cslfile ]
        )
        self.sock.send(pak)
    
    def remove(self, packagename, id=0):
        """Remove package's all scripts from system.
        """
        pak = self.__pack(self.__REMOVE, id, [ packagename ])
        self.sock.send(pak)
    
    def can_access(self, methodname, id=0):
        """Check if user has permission to call given method.
        """
        pak = self.__pack(self.__CHECKACL, id, [ methodname ])
        self.sock.send(pak)
    
    def call(self, methodname, args=None, id=0):
        """Make a configuration call on the system model.
        """
        a = [ methodname ]
        if args:
            if isinstance(args, dict):
                for key in args:
                    a.append(key)
                    a.append(args[key])
            else:
                a.extend(args)
        pak = self.__pack(self.__CALL, id, a)
        self.sock.send(pak)
    
    def call_package(self, methodname, packagename, args=None, id=0):
        """Make a configuration call directed to a package.
        """
        a = [ methodname, packagename ]
        if args:
            if isinstance(args, dict):
                for key in args:
                    a.append(key)
                    a.append(args[key])
            else:
                a.extend(args)
        pak = self.__pack(self.__CALL_PACKAGE, id, a)
        self.sock.send(pak)
    
    def cancel(self, id=0):
        """Cancel previously started operations.
        """
        pak = self.__pack(self.__CANCEL, id, [])
        self.sock.send(pak)
    
    def get_packages(self, classname, id=0):
        """Return registered packages for a given system model class.
        """
        pak = self.__pack(self.__GETLIST, id, [ classname ])
        self.sock.send(pak)
    
    def ask_notify(self, notifyname, id=0):
        """Ask for a notification event to be delivered.
        """
        pak = self.__pack(self.__ASKNOTIFY, id, [ notifyname ])
        self.sock.send(pak)
