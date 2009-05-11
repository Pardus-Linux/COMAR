# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2009, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

"""network module provides network management utils."""

import os
import subprocess

from pardus import iniutils

NET_PATH = "/etc/network"
NET_STACK = "baselayout"

INI = iniutils.iniParser(os.path.join(NET_PATH, script()))

def listProfiles():
    try:
        return INI.listSections()
    except iniutils.iniParserError:
        return []

class Profile:
    def __init__(self, name):
        self.name = name
        try:
            self.info = INI.getSection(name)
        except iniutils.iniParserError:
            self.info = {}

    def delete(self):
        INI.removeSection(self.name)

    def save(self, no_notify=False):
        is_new = self.name not in listProfiles()
        INI.setSection(self.name, self.info)
        if no_notify:
            return
        if is_new:
            notify("Network.Link", "connectionChanged", ("added", self.name))
        else:
            notify("Network.Link", "connectionChanged", ("changed", self.name))

class AccessPoint:
    def __init__(self, id=None):
        self.ssid = ""
        self.mode = ""
        self.mac = ""
        self.encryption = "none"
        self.qual = ""
        self.protocol = ""
        self.channel = ""
        if id:
            if " (" in id and id.endswith(")"):
                self.ssid, rest = id.split(" (", 1)
                self.mode, self.mac = rest.split(" ", 1)
                self.mac = self.mac[:-1]
            else:
                self.ssid = id

    def id(self):
        d = {
            "remote": self.ssid,
            "mode": self.mode,
            "mac": self.mac,
            "encryption": self.encryption,
            "quality": self.qual,
            "protocol": self.protocol,
            "channel": self.channel,
        }
        return d

def stopSameDevice(name):
    from csl import setState
    profile = Profile(name)
    device = profile.info["device"]
    for pn in listProfiles():
        if pn == name:
            continue
        pro = Profile(pn)
        if pro.info["device"] == device:
            setState(pn, "down")

def registerNameServers(profile, iface):
    name_mode = profile.info.get("name_mode", "default")
    name_servers = []
    name_domain = ""
    if name_mode == "auto":
        for server in iface.autoNameServers():
            name_servers.append(server)
        name_domain = iface.autoNameSearch()
    elif name_mode == "custom":
        for server in profile.info.get("name_server", ",").split():
           if server.strip():
               name_servers.append(server.strip())
    elif name_mode == "default":
        name_servers = call(NET_STACK, "Network.Stack", "getNameServers")
    call(NET_STACK, "Network.Stack", "registerNameServers", (iface.name, name_servers, name_domain))

def unregisterNameServers(iface):
    call(NET_STACK, "Network.Stack", "unregisterNameServers", (iface.name, [], ""))

def callScript(name, state):
    path = os.path.join("/etc/network/netlink.d", "%s.%s" % (name, state))
    if os.path.exists(path):
        try:
            subprocess.call([path])
        except:
            pass
