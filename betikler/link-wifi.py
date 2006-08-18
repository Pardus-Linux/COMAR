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
import re
import popen2
from comar import network

def capture(cmd):
    out = []
    a = popen2.Popen4(cmd)
    while 1:
        b = a.fromchild.readline()
        if b == None or b == "":
            break
        out.append(b)
    return (a.wait(), out)


class Wireless:
    """ ioctl stuff """

#   From </usr/include/wireless.h>
    
    SIOCSIWMODE = 0x8B06    # set the operation mode
    SIOCGIWMODE = 0x8B07    # get operation mode
    SIOCGIWRATE = 0x8B21    # get default bit rate
    SIOCSIWESSID = 0x8B1A   # set essid
    SIOCGIWESSID = 0x8B1B   # get essid
    
    modes = ['Auto', 'Ad-Hoc', 'Managed', 'Master', 'Repeat', 'Second', 'Monitor']

    def __init__(self):
        # create a socket to communicate with system
        self.sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _ioctl(self, func, args):
        return fcntl.ioctl(self.sockfd.fileno(), func, args)

    def _call(self, ifname, func, arg = None):

        if arg is None:
            data = (ifname + '\0' * 32)[:32]
        else:
            data = (ifname + '\0' * 16)[:16] + arg

        try:
            result = self._ioctl(func, data)
        except IOError:
            return None

        return result

    def _readsys(self, ifname, f):
        try:
            fp = file(os.path.join("/sys/class/net", ifname, f))
            result = fp.readline().rstrip('\n')
            fp.close()
        except IOError:
            return None
            
        return result

    def getInterfaceList(self):
        """ Find wireless interfaces """
        iflist = []
        path = "/sys/class/net" # FIXME: There may be an ioctl way to do this
        for interface in os.listdir(path):
            if os.path.exists(os.path.join(path, interface, "wireless")):
                iflist.append(interface)
        return iflist

    def getEssid(self, ifname):
        """ Get the ESSID for an interface """
        buffer = array.array('c', '\0' * 16)
        addr, length = buffer.buffer_info()
        arg = struct.pack('Pi', addr, length)

        self._call(ifname, self.SIOCGIWESSID, arg)
        return buffer.tostring().strip('\x00')

    def getMode(self, ifname):
        """ Get the operating mode of an interface """
        result = self._call(ifname, self.SIOCGIWMODE)
        mode = struct.unpack("i", result[16:20])[0]
        return self.modes[mode]

    def getBitrate(self, ifname):
        """ Get the bitrate of an interface """
        # Note for UI coder, KILO is not 2^10 in wireless tools world

        result = self._call(ifname, self.SIOCGIWRATE)

        size = struct.calcsize('ihbb')
        m, e, i, pad = struct.unpack('ihbb', result[16:16+size])
        if e == 0:
            bitrate =  m
        else:
            bitrate = float(m) * 10**e

        return bitrate

    def getLinkStatus(self, ifname):
        """ Get link status of an interface """
        link = self._readsys(ifname, "wireless/link")
        return int(link)

    def getNoiseStatus(self, ifname):
        """ Get noise level of an interface """
        noise = self._readsys(ifname, "wireless/noise")
        return int(noise) - 256

    def getSignalStatus(self, ifname):
        """ Get signal status of an interface """
        signal = self._readsys(ifname, "wireless/level")
        return int(signal) - 256

    def setEssid(self, ifname, essid):
        """ Set the ESSID for an interface """
        if len(essid) > 16:
            return "ESSID should be 16 char or less" # FIXME: How shall we define error messages ?

        arg = struct.pack("iHH", id(essid) + 20, len(essid) + 1, 1)
        self._call(ifname, self.SIOCSIWESSID, arg)

        if self.getEssid is essid:
            return True
        else:
            return None

    def setMode(self, ifname, mode):
        """ Set the operating mode of an interface """
        arg = struct.pack("l", self.modes.index(mode))
        self._call(ifname, self.SIOCSIWMODE, arg)

        if self.getMode is mode:
            return True
        else:
            return None


class Scanner:
    def __init__(self):
        self.list = []
    
    def _collect(self, m):
        # FIXME: what to do with <hidden> entries?
        self.list.append(m.group(1))
        return ""
    
    def scan(self, ifc):
        icfg = network.IF(ifc)
        if not icfg.isUp():
            # Some wireless drivers cant do the scan while
            # interface is down, doh :(
            icfg.setAddress("0.0.0.0")
            icfg.up()
        a = capture("/usr/sbin/iwlist %s scanning" % ifc)
        re.sub('ESSID:.*"(.*)"', self._collect, "\n".join(a[1]))
        return "\n".join(self.list)


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
        self.dev = None
        self.name = name
        if self.uid:
            self.ifc = network.findInterface(self.uid)
        self.state = _get(dict, "state", "down")
        self.remote = _get(dict, "remote", None)
        self.mode = _get(dict, "mode", "auto")
        self.address = _get(dict, "address", None)
        self.gateway = _get(dict, "gateway", None)
        self.mask = _get(dict, "mask", None)
        self.password = _get(dict, "password", None)
    
    def up(self):
        ifc = self.ifc
        if self.remote:
            wifi = Wireless()
            wifi.setEssid(ifc.name, self.remote)
        if self.password and self.password != "":
            os.system("/usr/sbin/iwconfig %s enc restricted %s" % (ifc.name, self.password))
        else:
            os.system("/usr/sbin/iwconfig %s enc off" % (ifc.name))
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
    
    ifc = network.IF(devname)
    if type == "add":
        if not ifc.isWireless():
            return
        devuid = ifc.deviceUID()
        notify("Net.Link.deviceChanged", "added wifi %s %s" % (devuid, network.deviceName(devuid)))
        conns = instances("name")
        for conn in conns:
            dev = Dev(conn)
            if dev.ifc and devuid == dev.ifc.deviceUID():
                if dev.state == "up":
                    dev.up()
                    return
                flag = 0
        if flag:
            notify("Net.Link.deviceChanged", "new wifi %s %s" % (devuid, network.deviceName(devuid)))
    
    elif type == "remove":
        conns = instances("name")
        for conn in conns:
            dev = Dev(conn)
            if dev.ifc and dev.ifc.name == devname:
                if dev.state == "up":
                    notify("Net.Link.stateChanged", dev.name + "\ndown")
        notify("Net.Link.deviceChanged", "removed wifi %s" % devname)

def modes():
    return "device,remote,scan,net,auto,passauth"

def linkInfo():
    return "\n".join([
        "wifi",
        "Wireless network",
        "ESS ID"
    ])

def deviceList():
    iflist = []
    for ifc in network.interfaces():
        if ifc.isWireless():
            uid = ifc.deviceUID()
            info = network.deviceName(uid)
            iflist.append("%s %s" % (uid, info))
    return "\n".join(iflist)

def scanRemote(device=None):
    a = Scanner()
    if device:
        ifc = network.findInterface(device)
        if ifc:
            device = ifc.name
    if not device:
        device = ""
    return a.scan(device)

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
    notify("Net.Link.connectionChanged", "configured remote " + name)

def setAuthentication(name=None, mode=None, user=None, password=None, key=None):
    pass

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

def getRemote(name=None):
    dev = Dev(name)
    if not dev:
        fail("No such connection")
    return name + "\n" + dev.remote

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

def getAuthentication(name=None):
    dev = Dev(name)
    if dev.password and dev.password != "":
        return "%s\npassauth\n%s" % (name, dev.password)
    return "%s\nnone" % name

def getState(name=None):
    dev = Dev(name)
    if not dev:
        fail("No such connection")
    return name + "\n" + dev.state
