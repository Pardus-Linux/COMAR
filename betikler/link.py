#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

import os
import array
import csapi
import popen2
from glob import glob
from comar.device import idsQuery
from comar import network


class Route:
    """ ioctl stuff """

    # From <bits/ioctls.h>

    SIOCADDRT = 0x890B      # add routing table entry
    SIOCDELRT = 0x890C      # delete routing table entry
    SIOCRTMSG = 0x890D      # call to routing system
    INADDR_ANY = '\0' * 4   # Any Internet Address

    def delRoute(self, gw, dst = "0.0.0.0", mask = "0.0.0.0"):
        """ Delete a route entry from kernel routing table """
        try:
            csapi.changeroute(self.SIOCDELRT, gw, dst, mask)
        except:
            pass

    def delDefaultRoute(self):
        """ Delete the default gw, which is a route entry with gateway to Any Internet Address """
        self.delRoute("0.0.0.0")

    def setDefaultRoute(self, gw, dst = "0.0.0.0", mask = "0.0.0.0"):
        """ Set the default gateway. To do this we must delete the previous default gateway
            and the route entry set for gw, if any, or we will end up with multiple entries """

        self.delDefaultRoute()
        self.delRoute(gw)
        try:
            csapi.changeroute(self.SIOCADDRT, gw, dst, mask)
        except:
            pass


class Dhcp:
    def _run(self, args):
        cmd = "/sbin/dhcpcd " + args
        a = popen2.Popen4(cmd)

        return a.wait() 

    def start(self, ifname, timeout = "30"):
        """ Start the DHCP client daemon """
        # Maybe we should leave this to GUI
        if ifname in self.getRunning():
            self.stop(ifname)

        # -R -Y -N to prevent dhcpcd rewrite nameservers
        #          we should add nameservers, not rewrite them
        # -H to set hostname due to info from server
        # -t for timeout

        args = "-R -Y -N -t " + timeout + " " + ifname
        return self._run(args)

    def stop(self, ifname):
        """ Stop DHCP client daemon """
        args = "-k " + ifname
        return self._run(args)

    def getNameServers(self, ifname):
        """ Get DNS server list provided by the server """
        info_file = "/var/lib/dhcpc/dhcpcd-" + ifname + ".info"

        try:
            f = file(info_file)
            for line in f.readlines():
                if not line.find("DNS="):
                    return line[line.find("DNS=")+4:].rstrip('\n').split(',')
            f.close()
        except IOError:
            return "Could not open file" # FIXME: put an error message here

    def getRunning(self):
        d = []
        for i in glob("/var/run/dhcpcd-*.pid"):
            d.append(i.rstrip(".pid").lstrip("/var/run/dhcpcd-"))
        return d



def sysValue(path, dir, file_):
    f = file(os.path.join(path, dir, file_))
    data = f.read().rstrip('\n')
    f.close()
    return data

def queryUSB(vendor, device):
    # dependency to pciutils!
    return idsQuery("/usr/share/misc/usb.ids", vendor, device)

def queryPCI(vendor, device):
    # dependency to pciutils!
    return idsQuery("/usr/share/misc/pci.ids", vendor, device)

# Internal functions

sysfs_path = "/sys/class/net"

def lremove(str, pre):
	if str.startswith(pre):
		return str[len(pre):]
	return str

def _device_uid_internal(dev):
    type, rest = sysValue(sysfs_path, dev, "device/modalias").split(":", 1)
    if type == "pci":
        vendor = lremove(sysValue(sysfs_path, dev, "device/vendor"), "0x")
        device = lremove(sysValue(sysfs_path, dev, "device/device"), "0x")
        id = "pci:%s_%s_%s" % (vendor, device, dev)
    elif type == "usb":
        for file_ in os.listdir(os.path.join(sysfs_path, dev, "device/driver")):
            if ":" in file_:
                path = dev + "/device/bus/devices/%s" % file_.split(":", 1)[0]
                vendor = sysValue(sysfs_path, path, "idVendor")
                device = sysValue(sysfs_path, path, "idProduct")
                id = "usb:%s_%s_%s" % (vendor, device, dev)
                break
        else:
            id = "usb:unknown_%s" % dev
    else:
        id = "%s:unknown_%s" % (type, dev)
    
    return id

def _device_uid(dev):
    try:
        id = _device_uid_internal(dev)
    except:
        id = "unk:unknown_%s" % dev
    
    return id

def _device_check(dev, uid):
    dev_uid = _device_uid(dev)
    t1 = dev_uid.rsplit("_", 1)
    t2 = uid.rsplit("_", 1)
    return t1[0] == t2[0]

def _device_dev(uid):
    t = uid.rsplit("_", 1)
    if _device_check(t[1], uid):
        return t[1]
    iflist = []
    for iface in os.listdir(sysfs_path):
        ifc = network.IF(iface)
        if ifc.isEthernet():
            iflist.append(_device_uid(iface))
    for dev in iflist:
        if _device_check(dev, uid):
            return dev
    return None

def _device_info(uid):
    t = uid.split(':', 1)
    if len(t) < 2:
        return "Unknown (%s)" % uid
    vendor, device, dev = t[1].split('_')
    if t[0] == "pci":
        return queryPCI(vendor, device)
    elif t[0] == "usb":
        return queryUSB(vendor, device)
    return "Unknown (%s)"

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
        self.dev = None
        if self.uid:
            self.dev = _device_dev(self.uid)
        self.state = _get(dict, "state", "down")
        self.mode = _get(dict, "mode", "auto")
        self.address = _get(dict, "address", None)
        self.gateway = _get(dict, "gateway", None)
        self.mask = _get(dict, "mask", None)
    
    def up(self):
        ifc = network.IF(self.dev)
        if self.mode == "manual":
            ifc.setAddress(self.address, self.mask)
            ifc.up()
            if self.gateway:
                route = Route()
                route.setDefaultRoute(self.gateway)
            notify("Net.Link.stateChanged", self.name + "\nup")
        else:
            dd = Dhcp()
            notify("Net.Link.stateChanged", self.name + "\nconnecting")
            dd.start(self.dev, timeout="20")
            if ifc.isUp():
                addr = ifc.getAddress()[0]
                notify("Net.Link.connectionChanged", "gotaddress " + self.name + "\n" + unicode(addr))
                notify("Net.Link.stateChanged", self.name + "\nup")
            else:
                notify("Net.Link.stateChanged", self.name + "\ndown")
                fail("DHCP failed")
    
    def down(self):
        if self.mode != "manual":
            dd = Dhcp()
            dd.stop(self.dev)
        ifc = network.IF(self.dev)
        ifc.down()
        notify("Net.Link.stateChanged", self.name + "\ndown")


def isWireless(devname):
    f = file("/proc/net/wireless")
    data = f.readlines()
    f.close()
    for line in data[2:]:
        name = line[:line.find(": ")].strip()
        if name == devname:
            return True
    return False


# Net.Link API

def kernelEvent(data):
    type, dir = data.split("@", 1)
    devname = lremove(dir, "/class/net/")
    flag = 1
    
    if type == "add":
        if isWireless(devname):
            return
        devuid = _device_uid(devname)
        notify("Net.Link.deviceChanged", "added net %s %s" % (devuid, _device_info(devuid)))
        conns = instances("name")
        for conn in conns:
            dev = Dev(conn)
            if dev.uid and devuid == dev.uid:
                if dev.state == "up":
                    dev.up()
                    return
                flag = 0
        if flag:
            notify("Net.Link.deviceChanged", "new net %s %s" % (devuid, _device_info(devuid)))
    
    elif type == "remove":
        conns = instances("name")
        for conn in conns:
            dev = Dev(conn)
            if dev.uid and dev.uid.rsplit("_", 1)[1] == devname:
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
    for iface in os.listdir(sysfs_path):
        ifc = network.IF(iface)
        if ifc.isEthernet():
            if not isWireless(iface):
                uid = _device_uid(iface)
                info = _device_info(uid)
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
