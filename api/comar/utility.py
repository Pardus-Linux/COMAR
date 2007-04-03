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

import os
import fcntl
import time
import subprocess


class execReply(int):
    def __init__(self, value):
        int.__init__(self, value)
        self.stdout = None
        self.stderr = None


def run(*cmd):
    """Run a command without running a shell"""
    command = []
    if len(cmd) == 1:
        if isinstance(cmd[0], basestring):
            command = cmd[0].split()
        else:
            command = cmd[0]
    else:
        command = cmd
    proc = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    reply = execReply(proc.wait())
    reply.stdout, reply.stderr = proc.communicate()
    return reply

def checkDaemon(pidfile):
    if not os.path.exists(pidfile):
        return False
    pid = file(pidfile).read().rstrip("\n")
    if len(pid) == 0 or len(filter(lambda x: not x in "0123456789", pid)) > 0:
        return False
    if not os.path.exists("/proc/%s" % pid):
        return False
    return True

def waitBus(unix_name, timeout=5, wait=0.1, stream=True):
    import socket
    if stream:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    else:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    while timeout > 0:
        try:
            sock.connect(unix_name)
            return True
        except:
            timeout -= wait
        time.sleep(wait)
    return False


class FileLock:
    def __init__(self, filename):
        self.filename = filename
        self.fd = None
    
    def lock(self, shared=False, timeout=-1):
        type_ = fcntl.LOCK_EX
        if shared:
            type_ = fcntl.LOCK_SH
        if timeout != -1:
            type_ |= fcntl.LOCK_NB
        
        self.fd = os.open(self.filename, os.O_WRONLY | os.O_CREAT, 0600)
        if self.fd == -1:
            raise "Cannot create lock file"
        
        while True:
            try:
                fcntl.flock(self.fd, type_)
                return
            except IOError:
                if timeout > 0:
                    time.sleep(0.2)
                    timeout -= 0.2
                else:
                    raise
    
    def unlock(self):
        fcntl.flock(self.fd, fcntl.LOCK_UN)
