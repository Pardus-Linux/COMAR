#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

import os
from comar import network

# Internal functions

def _get(dict, key, default):
    val = default
    if dict and dict.has_key(key):
        val = dict[key]
    return val


class Dev:
    def __init__(self, name):
        dict = get_instance("name", name)
        self.uid = _get(dict, "device", None)
        self.name = name
        self.ifc = None
        if self.uid:
            self.ifc = network.findInterface(self.uid)
        self.state = _get(dict, "state", "down")
        self.mode = _get(dict, "mode", "auto")
        self.address = _get(dict, "address", None)
        self.gateway = _get(dict, "gateway", None)
        self.mask = _get(dict, "mask", None)
    
    def up(self):
        ifc = self.ifc
        if self.mode == "manual":
            ifc.setAddress(self.address, self.mask)
            ifc.up()
            if self.gateway:
                route = network.Route()
                route.setDefault(self.gateway)
            notify("Net.Link.stateChanged", self.name + "\nup")
        else:
            notify("Net.Link.stateChanged", self.name + "\nconnecting")
            ifc.startAuto(timeout="20")
            if ifc.isUp():
                addr = ifc.getAddress()[0]
                notify("Net.Link.connectionChanged", "gotaddress " + self.name + "\n" + unicode(addr))
                notify("Net.Link.stateChanged", self.name + "\nup")
            else:
                notify("Net.Link.stateChanged", self.name + "\ndown")
                fail("DHCP failed")
    
    def down(self):
        ifc = self.ifc
        if self.mode != "manual":
            ifc.stopAuto()
        ifc.down()
        notify("Net.Link.stateChanged", self.name + "\ndown")


# Net.Link API

def kernelEvent(data):
    type, dir = data.split("@", 1)
    devname = lremove(dir, "/class/net/")
    flag = 1
    
    if type == "add":
        ifc = network.IF(devname)
        if ifc.isWireless():
            return
        devuid = ifc.deviceUID()
        notify("Net.Link.deviceChanged", "added net %s %s" % (devuid, network.deviceName(devuid)))
        conns = instances("name")
        for conn in conns:
            dev = Dev(conn)
            if dev.uid and devuid == dev.uid:
                if dev.state == "up":
                    dev.up()
                    return
                flag = 0
        if flag:
            notify("Net.Link.deviceChanged", "new net %s %s" % (devuid, network.deviceName(devuid)))
    
    elif type == "remove":
        conns = instances("name")
        for conn in conns:
            dev = Dev(conn)
            if dev.ifc and dev.ifc.name == devname:
                if dev.state == "up":
                    notify("Net.Link.stateChanged", dev.name + "\ndown")
        notify("Net.Link.deviceChanged", "removed net %s" % devname)

def modes():
    return "device,net,auto"

def linkInfo():
    return "\n".join([
        "net",
        "Ethernet network",
        ""
    ])

def deviceList():
    iflist = []
    for ifc in network.interfaces():
        if ifc.isEthernet() and not ifc.isWireless():
            uid = ifc.deviceUID()
            info = network.deviceName(uid)
            iflist.append("%s %s" % (uid, info))
    return "\n".join(iflist)

def scanRemote():
    fail("Not supported")

def setConnection(name=None, device=None):
    dict = get_instance("name", name)
    if dict and dict.has_key("device"):
        notify("Net.Link.connectionChanged", "configured device " + name)
    else:
        notify("Net.Link.connectionChanged", "added " + name)

def deleteConnection(name=None):
    dev = Dev(name)
    if dev.dev and dev.state == "up":
        dev.down()
    notify("Net.Link.connectionChanged", "deleted " + name)

def setAddress(name=None, mode=None, address=None, mask=None, gateway=None):
    dev = Dev(name)
    if dev.state == "up":
        dev.address = address
        dev.gateway = gateway
        dev.up()
    notify("Net.Link.connectionChanged", "configured address " + name)

def setRemote(name=None, remote=None):
    fail("Not supported")

def setState(name=None, state=None):
    dev = Dev(name)
    if state != "up" and state != "down":
        fail("unknown state")
    
    notify("Net.Link.connectionChanged", "configured state " + name)
    
    if not dev.dev:
        fail("Device not found")
    
    if state == "up":
        dev.up()
    else:
        if dev.state == "up":
            dev.down()

def connections():
    list = instances("name")
    if list:
        return "\n".join(list)
    return ""

def connectionInfo(name=None):
    dict = get_instance("name", name)
    if not dict:
        fail("No such connection")
    s = "\n".join([name, dict["device"], _device_info(dict["device"])])
    return s

def getAddress(name=None):
    dev = Dev(name)
    if not dev:
        fail("No such connection")

    if dev.mode == "auto":
        # FIXME: query interface
        s = "\n".join([name, dev.mode, '', ''])
    else:
        s = "\n".join([name, dev.mode, dev.address, dev.gateway])
        if dev.mask:
            s += "\n" + dev.mask
    return s

def getState(name=None):
    dev = Dev(name)
    if not dev:
        fail("No such connection")
    return name + "\n" + dev.state
