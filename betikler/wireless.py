#!/usr/bin/python
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

import array
import fcntl
import struct
import socket
import os

class wireless:
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

if __name__ == "__main__":
    wifi = wireless()
    ifaces_wifi = wifi.getInterfaceList()
    
    print "Wireless interfaces found = ", ifaces_wifi
    for name in ifaces_wifi:
        print " %s essid:%s mode:%s bitrate:%s b/s link:%i noise:%i dBm signal:%i dBm" % (name, wifi.getEssid(name), wifi.getMode(name), wifi.getBitrate(name),
            wifi.getLinkStatus(name), wifi.getNoiseStatus(name), wifi.getSignalStatus(name))

