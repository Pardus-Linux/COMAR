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
	op = "call"
	cslfile = "csl/sample/xorg.csl"
	omnode = "COMAR:Boot"
	appid = "DENEME"
	callEntry = "COMAR:Boot.ConfigureDisplay"
	remoteHost = "127.0.0.1:8000"
	objid = "test"
	objttsid = "TEST_03" + str(time.time())
	callttsid = "TEST_02" + str(time.time())
	x = 0
	skip = 0
	for i in sys.argv:
		if skip:
			skip = 0			
		elif i == "--help":
			print """
COMARd Test Client v 0.0.1

Usage:

for register a CSL file to OM:
  testclient.py --register [--file file][--node omnode][--appid appid]
  filename = Filename for CSL Code. Default: $PWD/csl/sample/xorg.csl
  node = OM Node for bind. Default: COMAR:Boot
  appid = Application ID. Default: DENEME		
for call OM Method Entry:
  testclient.py [--method methodName]
  method = Name of Method. Default: "COMAR:Boot.ConfigureDisplay"
Global Parameters:
  --parameter prm=val
  Add parameter "prm" with value "val" to call.
  --host ipAddr:port
  Host address for required COMARd daemon..
  --objtest objid
  OBJCALL Mode..
"""
			os._exit(0)
		elif i == "--register":
			op = "register"
		elif i == "--objtest":
			op = "objcall"
			objid = sys.argv[x+1]
			if callEntry == "COMAR:Boot.ConfigureDisplay":
				callEntry = "testEntry"
			skip = 1
		elif i == "--node":
			omnode = sys.argv[x+1]
			skip = 1
		elif i == "--appid":
			appid = sys.argv[x+1]
			skip = 1
		elif i == "--method":
			callEntry = sys.argv[x+1]
			skip = 1
		elif i == "--host":
			remoteHost = sys.argv[x+1]
			skip = 1 
		elif i == "--ttsid":
			callttsid = sys.argv[x+1]
			skip = 1 
		elif i == "--objttsid":
			objttsid = sys.argv[x+1]
			skip = 1 
		elif i == "--parameter":
			j = sys.argv[x+1]
			skip = 1
			print j
			key = j.split("=")[0]
			val = j.split("=")[1]
			print "Parameter '%s' value: %s" % (key, val)
			try:
				val = int(val)
				cval = COMARValue.numeric_create(val)
			except:
				cval = COMARValue.string_create(val)
			rpc.addPropertyMulti("parameter", key, cval)
		elif i == "--file":
			cslfile = sys.argv[x+1]
			skip = 1
		x += 1


	if op == "register":
		rpc.TTSID = callttsid
		rpc.RPCPriority = "INTERACTIVE"
		rpc.makeRPCData("OMCALL")
		rpc["name"] = "CORE:om.addNodeScript"
		rpc["type"] = "method"
		fname = cv.string_create(os.path.basename(cslfile))
		appid = cv.string_create(appid)
		f = open(cslfile)
		code = cv.string_create(f.read())
		f.close()
		node = cv.string_create(omnode)
		rpc.addPropertyMulti("parameter", "fileName", fname)
		rpc.addPropertyMulti("parameter", "code", code)
		rpc.addPropertyMulti("parameter", "AppID", appid)
		rpc.addPropertyMulti("parameter", "node", node)
	elif op == "objcall":
		rpc.TTSID = callttsid
		rpc.RPCPriority = "INTERACTIVE"
		rpc.makeRPCData("OBJCALL")
		print "Setting OBJ TTSID:", 
		rpc["ttsid"] = objttsid
		print rpc["ttsid"]
		rpc["object"] = cv.COMARValue(type="object", data = objid)
		rpc["name"] = callEntry
		rpc["type"] = "method"
	else:
		rpc.TTSID = callttsid
		rpc.RPCPriority = "INTERACTIVE"
		rpc.makeRPCData("OMCALL")
		rpc["name"] = callEntry
		rpc["type"] = "method"
	print "Send HTTP to localhost from:", os.getpid(), time.time(), rpc.xml
	print HTTP.makeConnection(realmAddress = remoteHost)
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
