#!/usr/bin/python
# -*- coding: utf-8 -*-
# COMARd	- COMAR Framework main VM.
# Copyright (c) 2003-2005 TUBITAK-UEKAE. All Rights Reserved.

# standart python modules
import os
import sys
import signal
import select
import time
import threading
import dircache
import md5
import traceback
import copy
import gdbm
import bsddb
import pwd
from errno import *

# COMAR modules
import comar_global # global values for COMAR
import COMARValue
import RPCData
import SESSION
import CHLDHELPER
import COMARAPI
import JOBSESS
import AUTHSYS

TA_CHLDS = None
CONNS = None
totalChild = 0
TA = None
DBIO = None
OM_MGR = None
TIMER  = None
FILEMON = None
PROCMON = None
AUTHHELPER = None

mkfname	= SESSION._makefilename

JOBSESS.comar_data = comar_global.comar_data
JOBSESS.comar_tadata = comar_global.comar_tadata

def initOM_MGR():
	global OM_MGR
	OM_MGR = COMARAPI.OM_MANAGER()

def createPID():
	global totalChild
	totalChild += 1
	return totalChild

CHLDHELPER.api_makepid = createPID

def initTAMGR():
	""" Create TA_MGR. """
	global TA_CHLDS, TA
	TA_CHLDS = CHLDHELPER.childHelper(None, 0, 0)
	TA = TAManager()

class COMARConnector(object):
	def __init__(self, module):
		self.mod = module
		self.object = module._CLIENT
		self.startCmd = getattr(module, module._START)
		self.stopCmd = getattr(module, module._STOP)
		self.blocked = module._BLOCKED
		self.proto = module.PROTOCOL
		self.runned = False
		self.pid = 0
		self.PID = 0
		self.IOChannel = None
		self.connData = {}

class ConnectorModules(object):
	def __init__(self, api_path=""):
		self.connectors = {}
		if api_path == "":
			api_path = comar_global.comar_modpath+"/connector"
		self.modpath = api_path
		self.activeConns = {}
		dl = dircache.listdir
		is_file = os.path.isfile
		files = dl(self.modpath)
		sys.path.insert(0, self.modpath)
		for file in files:
			fname = self.modpath + "/" + file
			if is_file(fname):
				if file[file.rfind("."):] == ".py":
					mod = self.loadModule(fname)
					if mod:
						self.connectors[mod.PROTOCOL] = { "module":mod, "obj":COMARConnector(mod) }

		sys.path.pop(0)

	def getModule(self, proto = "cxdrpc-http"):
		return self.connectors[proto]["obj"]
	def loadModule(self, module = "", modType="python"):
		if modType == "python":
			file = os.path.basename(module)
			file = file[:file.rfind('.')]
			if 1: #try:
				mod = __import__(file)
				if "PROTOCOL" in dir(mod) and "_CLIENT" in dir(mod) and mod._CLIENT != None:
					print "Connector loaded:", module
					return mod
				del mod # we are not going to use this anymore!
				return None
			else: #except:
				print "Invalid connector module '%s' denied" % (file)
				return None


def start():
	"""Starts COMARd"""
	global	CONNS, AUTHHELPER
	cv = COMARValue
	print "Initializing COMARd-client"
	if os.getuid():
		print "Only root can be use this program\nExiting.."
		os._exit(1)
	AUTHHELPER = AUTHSYS.authSystem()
	CONNS = ConnectorModules()
	HTTP = CONNS.getModule("cxdrpc-http").object(comarHelper = comarRoot())

	rpc = RPCData.RPCStruct()

	if "--register" in sys.argv:
		rpc.TTSID = "TEST_01" + str(time.time())
		rpc.RPCPriority = "INTERACTIVE"
		rpc.makeRPCData("OMCALL")
		rpc["name"] = "CORE:om.addNodeScript"
		rpc["type"] = "method"
		fname = cv.string_create("xorg.csl")
		appid = cv.string_create("DENEME")
		f = open("xorg.csl")
		code = cv.string_create(f.read())
		f.close()
		node = cv.string_create("COMAR:Boot")
		rpc.addPropertyMulti("parameter", "fileName", fname)
		rpc.addPropertyMulti("parameter", "code", code)
		rpc.addPropertyMulti("parameter", "AppID", appid)
		rpc.addPropertyMulti("parameter", "node", node)
	else:
		rpc.TTSID = "TEST_02" + str(time.time())
		rpc.RPCPriority = "INTERACTIVE"
		rpc.makeRPCData("OMCALL")
		rpc["name"] = "COMAR:Boot.ConfigureDisplay"
		rpc["type"] = "method"

	print "Send HTTP to localhost from:", os.getpid(), time.time()
	print HTTP.makeConnection(realmAddress = "127.0.0.1:8000")
	HTTP.sendRPC(rpc = rpc)

def stio2dict(strn):
	if strn == None:
		return None
	ret = {}
	cmds = strn.split("\x00")
	for item in cmds:
		if item.find("=") > -1:
			x = item.find("=")
			key = item[:x]
			val = item[x:]
			ret[key] = val
	return ret

class comarRoot:
	def __init__(self):
		self.createPID = createPID
		self.stio2dict = stio2dict
		self.authhelper= AUTHHELPER

if __name__ == "__main__":
	start()
