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
import socket
import fcntl
import struct

# From <bits/ioctls.h>
SIOCGIFFLAGS = 0x8913       # get flags
SIOCSIFFLAGS = 0x8914       # set flags
SIOCGIFADDR = 0x8915        # get PA address
SIOCSIFADDR = 0x8916        # set PA address
SIOCGIFNETMASK  = 0x891b    # get network PA mask
SIOCSIFNETMASK  = 0x891c    # set network PA mask
SIOCSIFMTU = 0x8922         # set MTU size

# From <net/if.h>
IFF_UP = 0x1                # Interface is up.
IFF_BROADCAST = 0x2         # Broadcast address valid.
IFF_DEBUG = 0x4             # Turn on debugging.
IFF_LOOPBACK = 0x8          # Is a loopback net.
IFF_POINTOPOINT = 0x10      # Interface is point-to-point link.
IFF_NOTRAILERS = 0x20       # Avoid use of trailers.
IFF_RUNNING = 0x40          # Resources allocated.
IFF_NOARP = 0x80            # No address resolution protocol.
IFF_PROMISC = 0x100         # Receive all packets.
IFF_ALLMULTI = 0x200        # Receive all multicast packets.
IFF_MASTER = 0x400          # Master of a load balancer.
IFF_SLAVE = 0x800           # Slave of a load balancer.
IFF_MULTICAST = 0x1000      # Supports multicast.
IFF_PORTSEL = 0x2000        # Can set media type.
IFF_AUTOMEDIA = 0x4000      # Auto media select active.


class IF:
    def __init__(self, ifname):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ifname = ifname
    
    def _ioctl(self, func, args):
        return fcntl.ioctl(self.sock.fileno(), func, args)
    
    def _call(self, func, ip = None):
        if ip:
            ifreq = (self.ifname + '\0' * 16)[:16]
            data = struct.pack("16si4s10x", ifreq, socket.AF_INET, socket.inet_aton(ip))
        else:
            data = (self.ifname + '\0'*32)[:32]
        try:
            result = self._ioctl(func, data)
        except IOError:
            return None
        return result
    
    def _sys(self, name):
        path = os.path.join("/sys/class/net", self.ifname, name)
        if os.path.exists(path):
            return file(path).read().rstrip("\n")
        else:
            return None
    
    def isUp(self):
        result = self._call(SIOCGIFFLAGS)
        flags, = struct.unpack('H', result[16:18])
        return (flags & IFF_UP) != 0
    
    def up(self):
        ifreq = (self.ifname + '\0' * 16)[:16]
        flags = IFF_UP | IFF_RUNNING | IFF_BROADCAST | IFF_MULTICAST
        data = struct.pack("16sh", ifreq, flags)
        result = self._ioctl(SIOCSIFFLAGS, data)
        return result
    
    def down(self):
        ifreq = (self.ifname + '\0' * 16)[:16]
        result = self._call(SIOCGIFFLAGS)
        flags, = struct.unpack('H', result[16:18])
        flags &= ~IFF_UP
        data = struct.pack("16sh", ifreq, flags)
        result = self._ioctl(SIOCSIFFLAGS, data)
        return result
    
    def getAddress(self):
        result = self._call(SIOCGIFADDR)
        addr = socket.inet_ntoa(result[20:24])
        result = self._call(SIOCGIFNETMASK)
        mask = socket.inet_ntoa(result[20:24])
        return (addr, mask)
    
    def setAddress(self, address=None, mask=None):
        if address:
            result = self._call(SIOCSIFADDR, address)
            if not result or socket.inet_ntoa(result[20:24]) is not address:
                return None
        if mask:
            result = self._call(SIOCSIFNETMASK, mask)
            if not result or socket.inet_ntoa(result[20:24]) is not mask:
                return None
        return True
    
    def getStats(self):
        tx_b = self._sys("statistics/tx_bytes")
        rx_b = self._sys("statistics/rx_bytes")
        tx_e = self._sys("statistics/tx_errors")
        rx_e = self._sys("statistics/rx_errors")
        return (tx_b, rx_b, tx_e, rx_e)
    
    def getMAC(self):
        return self._sys("address")
    
    def getMTU(self):
        return self._sys("mtu")
    
    def setMTU(self, mtu):
        ifreq = (self.ifname + '\0' * 16)[:16]
        data = struct.pack("16si", ifreq, mtu)
        result = self._ioctl(SIOCSIFMTU, data)
        if struct.unpack("16si", result)[1] is mtu:
            return True
        return None
