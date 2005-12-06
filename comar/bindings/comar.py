# -*- coding: utf-8 -*-
#
# Copyright (C) 2005, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import socket
import select
import struct

class Error(Exception):
    pass

class Link:
    """A class for communicating with comard."""
    
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
    
    def __init__(self, sockname="/var/run/comar.socket"):
        try:
            self.sock = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
            self.sock.connect(sockname)
        except:
            raise Error('Cannot connect to the COMAR daemon')
    
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
    
    def read(self):
        """Read a reply from comard.
        
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
        try:
            data = self.sock.recv(8)
        except:
            raise Error('Connection closed')
        head = struct.unpack('!ii', str(data))
        cmd = head[0] >> 24
        size = head[0] & 0x00ffffff
        if size:
            try:
                data = self.sock.recv(size)
            except:
                raise Error('Connection closed')
        else:
            data = None
        if cmd == self.RESULT:
            t = data.split(' ', 1)
            return (cmd, head[1], t[1], t[0])
        else:
            return (cmd, head[1], data)
    
    def read_cmd(self):
        """Read a reply from comard.
        
        This method behaves like read method, except that it waits until
        a full message comes from the COMAR daemon.
        """
        while 1:
            fds = select.select([self.sock], [], [])
            if fds[0] != []:
                break
        return self.read()
    
    def localize(self, localename):
        """Set the language for translated replies.
        
        Since comard has no way to detect caller's locale, this command
        is used for sending user's language to the comard. Afterwards,
        all the jobs started with API calls uses translated messages in
        their replies.
        
        You can get the localename parameter from locale.getlocale call.
        """
        pass
    
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
            a.extend(args)
        pak = self.__pack(self.__CALL, id, a)
        self.sock.send(pak)
    
    def call_package(self, methodname, packagename, args=None, id=0):
        """Make a configuration call directed to a package.
        """
        a = [ methodname, packagename ]
        if args:
            a.extend(args)
        pak = self.__pack(self.__CALL_PACKAGE, id, a)
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


# Test functions for basic COMAR functionality
# Useful for debugging

def test_basic(class_="Time.Clock", package="hwclock", script="../betikler/clock.py"):
    com = Link()
    print "Calling register..."
    com.register(class_, package, script)
    while 1:
        reply = com.read_cmd()
        print "Reply", reply
        if reply[0] == com.RESULT:
            break
        elif reply[1] == com.ERROR:
            print "Oops, test failed!"
            return
    print "Checking list..."
    com.get_packages(class_)
    while 1:
        reply = com.read_cmd()
        print "Reply", reply
        if reply[0] == com.RESULT:
            break
        elif reply[1] == com.ERROR:
            print "Oops, test failed!"
            return
    print "Removing the package..."
    com.remove(package)
    while 1:
        reply = com.read_cmd()
        print "Reply", reply
        if reply[0] == com.RESULT:
            break
        elif reply[1] == com.ERROR:
            print "Oops, test failed!"
            return
    print "Checking list again..."
    com.get_packages(class_)
    while 1:
        reply = com.read_cmd()
        print "Reply", reply
        if reply[0] == com.RESULT:
            break
        elif reply[1] == com.ERROR:
            print "Oops, test failed!"
            return
    print "Basic functionality is OK :)"
