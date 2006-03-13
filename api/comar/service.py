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

def is_on():
    from csl import get_profile
    s = get_profile("System.Service.setState")
    if s:
        state = s["state"]
    else:
        state = "off"
    
    return state

# default methods

def info():
    from csl import serviceType
    from csl import serviceDesc
    return "\n".join([serviceType, is_on(), serviceDesc])

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
