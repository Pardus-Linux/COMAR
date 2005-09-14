#!/usr/bin/python
# -*- coding: utf-8 -*-

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
