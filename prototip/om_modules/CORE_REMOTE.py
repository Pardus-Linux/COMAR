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

# COMAR_REMOTE.py
# 

import os, sys, time
import comar_global

class remoteSubsystem:
	def __init__(self, dbHelper = None, CV = None):
		self.remote_db = dbHelper.dbOpen(comar_global.comar_basic_data + "eventhnd.db")
		self.dbHelper = dbHelper
		self.CV = CV
		self.objHandlers = {}
		self.methodVtbl	 = {}
		self.propVtbl	= {}
		self.objDriver	= {}
		self.eventTag = 0
	def remoteSys_getClientRPCTypes(self, prms = {}, callerInfo = None):
		pass
	def remoteSys_getServerRPCTypes(self, prms = {}, callerInfo = None):
		pass
	def remoteSys_setDefaultForRealm(self, prms = {}, callerInfo = None):
		pass
	def remoteSys_getAddressForRealm(self, prms = {}, callerInfo = None):
		pass
	def remoteSys_addAddressForRealm(self, prms = {}, callerInfo = None):
		pass
	def remoteSys_delAddressForRealm(self, prms = {}, callerInfo = None):
		pass
	def remoteSys_addRealm(self, prms = {}, callerInfo = None):
		pass
