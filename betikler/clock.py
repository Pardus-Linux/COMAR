#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import os
import popen2
import csapi

# api
def capture(cmd):
	out = []
	a = popen2.Popen4(cmd)
	while 1:
		b = a.fromchild.readline()
		if b == None or b == "":
			break
		out.append(b)
	return (a.wait(), out)

# real script

tz_file = "/etc/localtime"
tz_zones = "/usr/share/zoneinfo/"

def getTimeZone():
    if os.path.islink(tz_file):
        path = os.path.realpath(tz_file)
        if path[:len(tz_zones)] == tz_zones:
            path = path[len(tz_zones):]
        # else?
        return path
    else:
        # KDE copies timezone data for supporting nfs mounted /usr partitions
        # we dont :)
        # anyone knows how to extract zone name from zoneinfo file?
        return "Switch again please"

def setTimeZone(zone=None):
    if zone:
        os.unlink(tz_file)
        os.symlink(os.path.join(tz_zones, zone), tz_file)

def setDate(year=None, month=None, day=None, hour=None, minute=None, second=None):
    new = list(time.localtime())
    if year: new[0] = int(year)
    if month: new[1] = int(month)
    if day: new[2] = int(day)
    if hour: new[3] = int(hour)
    if minute: new[4] = int(minute)
    if second: new[5] = int(second)
    csapi.settimeofday(time.mktime(new))

def getDate():
    return time.strftime("%Y %m %d %H %M %S %Z")

def saveToHW():
    capture("/sbin/hwclock --systohc")

def loadFromHW():
    capture("/sbin/hwclock --hctosys")
