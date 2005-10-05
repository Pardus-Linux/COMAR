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
def getTimeZone():
    print "bork"

def setTimeZone():
    print "dork"

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
    pass

def loadFromHW():
    pass
