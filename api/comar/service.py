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
import subprocess

# utility functions

def run(*cmd):
    """Run a command without running a shell"""
    if len(cmd) == 1:
        if isinstance(cmd[0], basestring):
            return subprocess.call(cmd[0].split())
        else:
            return subprocess.call(cmd[0])
    else:
        return subprocess.call(cmd)

def checkDaemon(pidfile):
    if not os.path.exists(pidfile):
        return False
    pid = file(pidfile).read().rstrip("\n")
    if not os.path.exists("/proc/%s" % pid):
        return False
    return True

def is_on():
    from csl import get_profile
    s = get_profile("System.Service.setState")
    if s:
        state = s["state"]
    else:
        state = "off"
    
    return state

def loadEnvironment():
    if os.path.exists("/etc/profile.env"):
        for line in file("/etc/profile.env"):
            if line.startswith("export "):
                key, value = line[7:].strip().split("=", 1)
                os.environ[key] = value[1:-1]

# default methods

def info():
    from csl import serviceType
    from csl import serviceDesc
    state = is_on()
    try:
        from csl import status
        if status():
            if state == "off":
                state = "started"
        else:
            if state == "on":
                state = "stopped"
    except:
        pass
    return "\n".join([serviceType, state, serviceDesc])

def ready():
    if is_on() == "on":
        from csl import start
        start()

def setState(state=None):
    if state == "on":
        from csl import start
        start()
    elif state == "off":
        from csl import stop
        stop()
    else:
        fail("Unknown state '%s'" % state)
