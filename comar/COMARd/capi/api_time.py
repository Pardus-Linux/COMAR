#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2004, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

# COMARd
# time related CAPI calls

import time

def	APICLASS():
	return "TIME"

_APICLASS  = "TIME"

def dummycheckPerms(*prm):
	return 1
	
class TIMEH:
	def __init__(self, IAPI, COMARValue):
		self.IAPI = IAPI
		self.cv = COMARValue
		self.objHandlers = {}
	
	def	GetFuncTable(self):
		return { 'settime':self.settime }
	
	def settime(self, _name = "", prms = {}, checkPerms=dummycheckPerms, callerInfo=None):
		teh = time.gmtime(time.time())
		keylist = prms.keys()
		for prm in keylist:
			if prm == "year":
				a = prms[prm].data.value
				print "YEAR:", a
			elif prm == "month":
				a = prms[prm].data.value
				print "MONTH:", a
		return self.cv.COMARRetVal( value=None, result=0 )


API_MODS = [ TIMEH ]
