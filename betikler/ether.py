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

import os

# internal funcs

ARPHRD_ETHER = 1

def atoi(s):
	# python'da bunu yapacak fonksiyon bulamadım
	# int() sayı olmayan karaktere rastladığında pörtlüyor
	t = ""
	for c in s.lstrip():
		if c in "0123456789":
			t += c
		else:
			break
	try:
		ret = int(t)
	except:
		ret = 0
	return ret

def sysValue(path, dir, file_):
    f = file(os.path.join(path, dir, file_))
    data = f.read().rstrip('\n')
    f.close()
    return data

def queryPCI(vendor, device):
    # dependency to pciutils!
    f = file("/usr/share/misc/pci.ids")
    flag = 0
    company = ""
    for line in f.readlines():
        if flag == 0:
            if line.startswith(vendor):
                flag = 1
                company = line[5:].strip("\n")
        else:
            if line.startswith("\t"):
                if line.startswith("\t" + device):
                    return company + line[6:].strip("\n")
            else:
                flag = 0
    return "Unknown"

# Net.Link API

def getActiveLinks():
        iflist = []
        path = "/sys/class/net"
        for iface in os.listdir(path):
            if atoi(sysValue(path, iface, "type")) == ARPHRD_ETHER:
                ifdata = iface + " net"
                if atoi(sysValue(path, iface, "flags")) & 0x1:
                    ifdata += " up"
                else:
                    ifdata += " down"
                vendor = sysValue(path, iface, "device/vendor").lstrip('0x')
                device = sysValue(path, iface, "device/device").lstrip('0x')
                ifdata += " " + vendor + ":" + device
                ifdata += queryPCI(vendor, device)
                iflist.append(ifdata)
        return "\n".join(iflist)
