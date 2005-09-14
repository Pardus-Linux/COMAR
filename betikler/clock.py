#!/usr/bin/python
# -*- coding: utf-8 -*-

import comar

import time
import os
import popen2

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
    # it seems python is missing settimeofday
    # i'll add it to the api and remove this ugly hack
    a = capture("/usr/bin/date " + time.strftime("%m%d%H%M%Y.%S", new))
    return a[1][0]

def getDate():
    comar.notify("Time.Clock.lala")
    return time.strftime("%Y %m %d %H %M %S %Z")

def saveToHW():
    pass

def loadFromHW():
    pass
