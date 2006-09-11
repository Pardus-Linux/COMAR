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

from comar.utility import *

# utility functions

def is_on():
    state = "off"
    s = get_profile("System.Service.setState")
    if s:
        state = s["state"]
    else:
        try:
            from csl import serviceDefault
            state = serviceDefault
        except:
            pass
    return state

def loadConfig():
    try:
        from csl import serviceConf
    except:
        serviceConf = script()[0]
    dict = {}
    try:
        for line in file("/etc/conf.d/%s" % serviceConf):
            if line != "" and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if value.startswith('"') or value.startswith("'"):
                    value = value[1:-1]
                dict[key] = value
    except:
        pass
    return dict

def loadEnvironment():
    basePath = "/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:"
    if os.path.exists("/etc/profile.env"):
        for line in file("/etc/profile.env"):
            if line.startswith("export "):
                key, value = line[7:].strip().split("=", 1)
                os.environ[key] = value[1:-1]
    # PATH in profile.env doesn't have some default paths
    os.environ["PATH"] = basePath + os.environ.get("PATH", "")

config = loadConfig()

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
