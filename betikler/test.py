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
import sys

SIOCSIFADDR = 0x8916

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

ifname = ("eth0" + '\0'*16)[:16]
print "[", ifname, "]", len(ifname)
args = struct.pack("16si4s10x", ifname, socket. AF_INET, socket.inet_aton("192.168.3.147"))
print args, len(args)

fcntl.ioctl(sock.fileno(), SIOCSIFADDR, args)
