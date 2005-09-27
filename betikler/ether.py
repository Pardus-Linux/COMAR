#!/usr/bin/python
# -*- coding: utf-8 -*-

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

# Net.Link API

def getActiveLinks():
        iflist = []
        path = "/sys/class/net"
        for iface in os.listdir(path):
            if atoi(sysValue(path, iface, "type")) == ARPHRD_ETHER:
                iflist.append(iface)
        return "\n".join(iflist)
