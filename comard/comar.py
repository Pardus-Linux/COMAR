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
    DENIED = 2
    RESULT_START = 3
    RESULT_END = 4
    NOTIFY = 5
    # following cmds are sent by internal methods, thus not visible to outside
    __LOCALIZE = 6
    __REGISTER = 7
    __REMOVE = 8
    __CALL = 9
    __CHECKACL = 10
    
    def __init__(self, sockname="/tmp/comar"):
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
        is a tuple of three items: (command, id, data)
        
        Command is a reply code defined at the start of this class.
        ID is the original id value from the request sent to the comard.
        Data is the return value in string format.
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
        return (cmd, head[1], data)
    
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
        pak =self.__pack(self.__CALL, id, a)
        self.sock.send(pak)
    
    def call_package(self, methodname, packagename, args, id=0):
        """Make a configuration call directed to a package.
        """
        pass
    
    def call_instance(self, methodname, packagename, instancename, args, id=0):
        # not yet decided
        pass
    
    def get_packages(self, classname, id=0):
        """Return registered packages for a given system model class.
        """
        pass
    
    def ask_notify(self, notifyname, id=0):
        """Ask for a notification event to be delivered.
        """
        pass
