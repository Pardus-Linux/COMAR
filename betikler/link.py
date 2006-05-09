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
import fcntl
import struct
import socket
import csapi
import popen2
from glob import glob
from comar.device import idsQuery

class ifconfig:
    """ ioctl stuff """

    IFNAMSIZ = 16               # interface name size

    # From <bits/ioctls.h>

    SIOCGIFADDR = 0x8915        # get PA address
    SIOCGIFBRDADDR  = 0x8919    # get broadcast PA address
    SIOCGIFCONF = 0x8912        # get iface list
    SIOCGIFFLAGS = 0x8913       # get flags
    SIOCGIFMTU = 0x8921         # get MTU size
    SIOCGIFNETMASK  = 0x891b    # get network PA mask
    SIOCSIFADDR = 0x8916        # set PA address
    SIOCSIFBRDADDR  = 0x891a    # set broadcast PA address
    SIOCSIFFLAGS = 0x8914       # set flags
    SIOCSIFMTU = 0x8922         # set MTU size
    SIOCSIFNETMASK  = 0x891c    # set network PA mask

    # From <net/if.h>    

    IFF_UP = 0x1           # Interface is up.
    IFF_BROADCAST = 0x2    # Broadcast address valid.
    IFF_DEBUG = 0x4        # Turn on debugging.
    IFF_LOOPBACK = 0x8     # Is a loopback net.
    IFF_POINTOPOINT = 0x10 # Interface is point-to-point link.
    IFF_NOTRAILERS = 0x20  # Avoid use of trailers.
    IFF_RUNNING = 0x40     # Resources allocated.
    IFF_NOARP = 0x80       # No address resolution protocol.
    IFF_PROMISC = 0x100    # Receive all packets.
    IFF_ALLMULTI = 0x200   # Receive all multicast packets.
    IFF_MASTER = 0x400     # Master of a load balancer.
    IFF_SLAVE = 0x800      # Slave of a load balancer.
    IFF_MULTICAST = 0x1000 # Supports multicast.
    IFF_PORTSEL = 0x2000   # Can set media type.
    IFF_AUTOMEDIA = 0x4000 # Auto media select active.


    def __init__(self):
        # create a socket to communicate with system
        self.sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _ioctl(self, func, args):
        return fcntl.ioctl(self.sockfd.fileno(), func, args)

    def _call(self, ifname, func, ip = None):

        if ip is None:
            data = (ifname + '\0'*32)[:32]
        else:
            ifreq = (ifname + '\0' * self.IFNAMSIZ)[:self.IFNAMSIZ]
            data = struct.pack("16si4s10x", ifreq, socket.AF_INET, socket.inet_aton(ip))

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
        """ Get all interface names in a list """
        # get interface list
        buffer = array.array('c', '\0' * 1024)
        ifconf = struct.pack("iP", buffer.buffer_info()[1], buffer.buffer_info()[0])
        result = self._ioctl(self.SIOCGIFCONF, ifconf)

        # loop over interface names
        iflist = []
        size, ptr = struct.unpack("iP", result)
        for idx in range(0, size, 32):
            ifconf = buffer.tostring()[idx:idx+32]
            name, dummy = struct.unpack("16s16s", ifconf)
            name, dummy = name.split('\0', 1)
            iflist.append(name)

        return iflist

    def getAddr(self, ifname):
        """ Get the inet addr for an interface """
        result = self._call(ifname, self.SIOCGIFADDR)
        return socket.inet_ntoa(result[20:24])

    def getNetmask(self, ifname):
        """ Get the netmask for an interface """
        result = self._call(ifname, self.SIOCGIFNETMASK)
        return socket.inet_ntoa(result[20:24])

    def getBroadcast(self, ifname):
        """ Get the broadcast addr for an interface """
        result = self._call(ifname, self.SIOCGIFBRDADDR)
        return socket.inet_ntoa(result[20:24])

    def getStatus(self, ifname):
        """ Check whether interface is UP """
        result = self._call(ifname, self.SIOCGIFFLAGS)
        flags, = struct.unpack('H', result[16:18])
        return (flags & self.IFF_UP) != 0

    def getMTU(self, ifname):
        """ Get the MTU size of an interface """
        data = self._call(ifname, self.SIOCGIFMTU)
        mtu = struct.unpack("16si12x", data)[1]
        return mtu

    def getMAC(self, ifname):
        """ Get MAC address of an interface """
        mac = self._readsys(ifname, "address")
        return mac

    def getRX(self, ifname):
        """ Get received bytes of an interface """
        rx = self._readsys(ifname, "statistics/rx_bytes")
        return int(rx)

    def getTX(self, ifname):
        """ Get transferred bytes of an interface """
        tx = self._readsys(ifname, "statistics/tx_bytes")
        return int(tx)

    def setAddr(self, ifname, ip):
        """ Set the inet addr for an interface """
        result = self._call(ifname, self.SIOCSIFADDR, ip)

        if result and socket.inet_ntoa(result[20:24]) is ip:
            return True
        else:
            return None

    def setNetmask(self, ifname, ip):
        """ Set the netmask for an interface """
        result = self._call(ifname, self.SIOCSIFNETMASK, ip)

        if result and socket.inet_ntoa(result[20:24]) is ip:
            return True
        else:
            return None

    def setBroadcast(self, ifname, ip):
        """ Set the broadcast addr for an interface """
        result = self._call(ifname, self.SIOCSIFBRDADDR, ip)

        if socket.inet_ntoa(result[20:24]) is ip:
            return True
        else:
            return None

    def setStatus(self, ifname, status):
        """ Set interface status (UP/DOWN) """
        ifreq = (ifname + '\0' * self.IFNAMSIZ)[:self.IFNAMSIZ]

        if status is "UP":
            flags = self.IFF_UP
            flags |= self.IFF_RUNNING
            flags |= self.IFF_BROADCAST
            flags |= self.IFF_MULTICAST
            flags &= ~self.IFF_NOARP
            flags &= ~self.IFF_PROMISC
        elif status is "DOWN":
            result = self._call(ifname, self.SIOCGIFFLAGS)
            flags, = struct.unpack('H', result[16:18])
            flags &= ~self.IFF_UP
        else:
            return None

        data = struct.pack("16sh", ifreq, flags)
        result = self._ioctl(self.SIOCSIFFLAGS, data)
        return result

    def setMTU(self, ifname, mtu):
        """ Set the MTU size of an interface """
        ifreq = (ifname + '\0' * self.IFNAMSIZ)[:self.IFNAMSIZ]

        data = struct.pack("16si", ifreq, mtu)
        result = self._ioctl(self.SIOCSIFMTU, data)

        if struct.unpack("16si", result)[1] is mtu:
            return True
        else:
            return None


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

ARPHRD_ETHER = 1
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
        if csapi.atoi(sysValue(sysfs_path, iface, "type")) == ARPHRD_ETHER:
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
        ifc = ifconfig()
        if self.mode == "manual":
            if self.address:
                ifc.setAddr(self.dev, self.address)
            if self.mask:
                ifc.setNetmask(self.dev, self.mask)
            ifc.setStatus(self.dev, "UP")
            if self.gateway:
                route = Route()
                route.setDefaultRoute(self.gateway)
            notify("Net.Link.stateChanged", self.name + "\nup")
        else:
            dd = Dhcp()
            notify("Net.Link.stateChanged", self.name + "\nconnecting")
            dd.start(self.dev, timeout="20")
            if ifc.getStatus(self.dev):
                addr = ifc.getAddr(self.dev)
                notify("Net.Link.connectionChanged", "gotaddress " + self.name + "\n" + unicode(addr))
                notify("Net.Link.stateChanged", self.name + "\nup")
            else:
                notify("Net.Link.stateChanged", self.name + "\ndown")
                fail("DHCP failed")
    
    def down(self):
        if self.mode != "manual":
            dd = Dhcp()
            dd.stop(self.dev)
        ifc = ifconfig()
        ifc.setStatus(self.dev, "DOWN")
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
        if csapi.atoi(sysValue(sysfs_path, iface, "type")) == ARPHRD_ETHER:
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
