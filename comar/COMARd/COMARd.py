#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2004, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.

# COMARd.py
# COMAR Framework main VM.

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
import AUTHSYS
import SESSION
import CHLDHELPER
import COMARAPI
import JOBSESS
import DBWORKER

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
COMARHELPER = None
mkfname	= SESSION._makefilename
DB_THREAD = 0
root_dbs = []
root_dbfd = []

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
	TA_CHLDS = CHLDHELPER.childHelper(None, 0, 0, "ROOT")
	TA = TAManager()

class COMARConnector(object):
	def __init__(self, module):
		self.mod = module
		self.object = module._OBJ
		self.startCmd = getattr(module, module._START)
		self.stopCmd = getattr(module, module._STOP)
		self.blocked = module._BLOCKED
		self.proto = module.PROTOCOL
		self.runned = False
		self.pid = 0
		self.PID = 0
		self.IOChannel = None
		self.connData = {}
		self.sessDHnds = { "IRSU_STD": self.addSessionData, "IRSU_RTD": self.reqSessionData, "IRSU_PTD":self.popSessionData }

	def _readFDSet(self):
		if self.runned:
			return [ self.IOChannel.cmd_rfile ]
		else:
			return []

	ReadFDs	= property(_readFDSet, None, None, None)

	def readData(self):
		if self.IOChannel.cmdReady():
			ret = self.IOChannel.getCommand() # this is (PID, TID, CMD, DATA) or None
			if ret != None:
				#d2 print "DATA:", ret
				return ret
		return None
	def sendData(self, cmd, PID, TID, data):
		if self.IOChannel.pipeEmpty():
			ret = self.IOChannel.putCommand(cmd, PID, TID, data) # this is (PID, TID, CMD, DATA) or None
			#d2 print self.IOChannel.mode, "CONN SEND DATA:", ret
			return ret
		print "IPC Connection timeout !!"
		return None
	def start(self):
		if self.runned:
			return
		PID = createPID()
		IO = SESSION.COMARPipe()
		self.pid = os.fork()
		if self.pid:	# Parent..
			IO.debug = 0
			IO.name  =  "COMARD-->CONN:"+self.proto
			IO.initFor("parent")
			self.PID = PID
			self.runned = True
			self.IOChannel = IO
			#TA_CHLDS.registerChild(PID, 0)
			return IO
		else:	# Client
			print "Connector Module (%d/%d) for '%s' protocol is started.." % (PID, os.getpid(), self.proto)
			IO.debug = 0
			IO.name =  "COMARD-->CONN:" + self.proto
			IO.initFor("client")
			#try:
			obj = self.object()
			select.select([],[],[], 0.1)
			self.startCmd(obj, PID, 0, IO)
			#except:
			print "Connector Module '%s' with PID: %d terminated abnormally.." % (self.proto, PID)
			os._exit(0)
	def stop(self):
		if not self.runned:
			return
		if self.blocked:
			self.IOChannel.putCommand("LNSU_KILL")
			st = time.time() + 3
			while time.time() < st:
				if os.WIFEXITED(os.waitpid(self.pid, os.WNOHANG)):
					self.runned = 0
					break
			if self.runned:
				os.kill(self.pid, signal.SIGKILL)
				api_select.select( [],[],[], 0.5)
				self.runned = 0
			self.pid = 0
			self.PID = 0
			self.IOChannel.destroy()
			return
	def sessDataHnd(self, cmd, data):
		if self.sessDHnds.has_key(cmd):
			return self.sessDHnds[cmd](data)
	def addSessionData(self, data):
		# <session_id[<=32]> <key[<=32]> <eol> <data[...]>
		global TIMER
		psid = data.find(" ")
		pkey = data.find(" ", psid + 1)
		peol = data.find(" ", pkey + 1)
		pdata = data.find(" ", peol + 1)
		sid = data[0:psid]
		key = data[psid+1:pkey]
		eol = data[pkey+1:peol]
		dta = data[peol+1:]
		print "ASD sid:'%s' key:'%s' eol:'%s' dta:'%s':" % (sid, key, eol, dta)
		if not self.connData.has_key(sid):
			self.connData[sid] = {}
		elif len(self.connData[sid]) > 16:
			return
		self.connData[sid][key] = (int(int(eol) + time.time()), dta)
		TIMER.addPeriodCall(self.cleanUData)
		print self.connData
	def cleanUData(self):
		t = int(time.time())
		delItems = []
		for s in self.connData.keys():
			for d in self.connData[s].keys():
				if self.connData[s][d][0] and self.connData[s][d][0] <= t:
					#print "Del:", self.connData[s][d][0], t
					delItems.append((s, d))
		for s in delItems:
			#print "Timeout: ", s, d, self.connData[s[0]][s[1]], self.connData
			del self.connData[s[0]][s[1]]
			if len(self.connData[s[0]]) == 0:
				del self.connData[s[0]]
		#print "After Timeout Check:",  self.connData
		if len(self.connData) == 0:
			#print "A Had delete we from event que"
			TIMER.delPeriodCall(self.cleanUData)

	def reqSessionData(self, data):
		psid = data.find(" ")
		pkey = data.find(" ", psid + 1)
		sid = data[0:psid]
		key = data[psid+1:]
		if not self.connData.has_key(sid):
			return None
		return self.connData[sid][key][1]

	def popSessionData(self, data):
		psid = data.find(" ")
		pkey = data.find(" ", psid + 1)
		sid = data[0:psid]
		key = data[psid+1:peol]
		if not self.connData.has_key(sid):
			return None
		ret = self.connData[sid][key][1][:]
		del self.connData[sid][key]
		if len(self.connData[sid]) == 0:
			del self.connData[sid]
		return ret

class ConnectorModules(object):
	def __init__(self, api_path=""):
		self.connectors = {}
		if api_path == "":
			api_path = comar_global.comar_modpath+"/connector"
		self.modpath = api_path
		self.activeConns = {}
		self.TAInf = {}
		self.TAInx = {}
		self.TIDsofPID = {}

	def sessDataHandler(self, cmd, PID, TID, data):
		global TA_CHLDS
		pi = str(PID) + ":" + str(TID)
		if self.activeConns.has_key(pi):
			print "Call conn data", cmd, data
			xPID = self.activeConns[pi][0]
			for i in self.connectors.keys():
				print "Scan:", self.connectors[i]["obj"].PID, xPID
				if self.connectors[i]["obj"].PID == xPID:
					return (PID, TID, "IRSU_GTD", self.connectors[i]["obj"].sessDataHnd(cmd, data))

		print "CONN Not Found :", pi, self.activeConns

	def connPID(self, PID, TID = None):
		if TID == None:
			for i in self.activeConns.keys():
				if int(i[:i.find(":")]) == PID:
					return PID
		else:
			pi = str(PID) + ":" + str(TID)
			if self.activeConns.has_key(pi):
				return self.activeConns[pi]

	def setLinkOffline(self, PID, TID, status):
		pi = str(PID) + ":" + str(TID)
		if self.activeConns.has_key(pi):			
			del self.activeConns[pi]
			if self.TAInx.has_key(pi):
				del self.TAInf[self.TAInx[pi]]
				del self.TAInx[pi]
		if self.TIDsofPID.has_key(PID):
			pos = 0
			x = 0
			for i in self.TIDsofPID[PID]:
				if i == TID:
					pos = x
					break
				x += 1
			del self.TIDsofPID[PID][pos]
			if len(self.TIDsofPID[PID]) == 0:
				del self.TIDsofPID[PID]
	def setAllOffLine(self, PID):
		x = self.TIDsofPID[PID][:]
		for i in x:
			self.setLinkOffline(PID, i)

	def addConnEntry(self, PID, TID, ConPID, connInfo, user, parent):
		print "Add Conn Entry: " , PID, TID, ConPID, connInfo, user
		self.activeConns[str(PID) + ":" + str(TID)] = [ConPID+0, connInfo, user, PID]
		if self.TIDsofPID.has_key(PID):
			self.TIDsofPID[PID].append(TID)
		else:
			self.TIDsofPID[PID] = [ TID ]
			

	def connInfo(self, xPID, xTID):
		key = str(xPID) + ":" + str(xTID)
		if self.activeConns.has_key(key):
			return self.activeConns[key][1]
		return None

	def setTAInfo(self, PID, TID, ttsKey):
		pi = str(PID) + ":" + str(TID)
		if self.activeConns.has_key(pi):
			self.TAInf[ttsKey] = (self.activeConns[pi][0], PID, TID)
			self.TAInx[pi] = ttsKey

	def getTAConn(self, ttsKey):
		if self.TAInf.has_key(ttsKey):
			return self.TAInf[ttsKey]

	def getUser(self, PID, TID):
		pi = str(PID) + ":" + str(TID)
		if self.activeConns.has_key(pi):
			return self.activeConns[pi][2]
		else:
			return None

	def setUser(self, PID, TID, user):
		pi = str(PID) + ":" + str(TID)
		if self.activeConns.has_key(pi):
			self.activeConns[pi][2] = user

	def init(self):
		global COMARHELPER
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
						mod.COMARHELPER = COMARHELPER
						self.connectors[mod.PROTOCOL] = { "module":mod, "obj":COMARConnector(mod) }
						self.connectors[mod.PROTOCOL]["obj"].start()
						
		sys.path.pop(0)

	def loadModule(self, module = "", modType="python"):
		""" Load a CAPI Module.."""
		if modType == "python":
			file = os.path.basename(module)
			file = file[:file.rfind('.')]
			try:
				mod = __import__(file)
				if "PROTOCOL" in dir(mod):
					print "Connector loaded:", module
					return mod
				del mod # we are not going to use this anymore!
				return None
			except:
				print "Invalid connector module '%s' denied" % (file)
				return None

	def readConn(self, xPID):
		for i in self.connectors.keys():
			conn = self.connectors[i]["obj"]
			if conn.PID == xPID:
				#print "Receive from:", i, xPID
				return conn.readData()				

	def sendTarget(self, command, PID = 0, TID = 0, data = None):
		pi = str(PID) + ":" + str(TID)
		if self.activeConns.has_key(pi):
			#print "Target Sender:", self.activeConns[pi][0], command, PID, TID, data
			self.sendConn(self.activeConns[pi][0], command, PID, TID, data)
		else:
			print "Critical Error: PID(%s)/TID(%s) Not registered to conns table" % (PID, TID)
			print "-" * 40
			print "Stack Trace:"
			print traceback.print_stack()

	def sendConn(self, ConnPID, command, PID = 0, TID = 0, data = None):
		for i in self.connectors.keys():
			if self.connectors[i]["obj"].PID == ConnPID:
				#print "Send To:", i, ConnPID
				return self.connectors[i]["obj"].sendData(command, PID, TID, data)

	def readfd2PID(self, fd):
		for i in self.connectors.keys():
			if fd in self.connectors[i]["obj"].ReadFDs:
				return self.connectors[i]["obj"].PID
		return 0

	def fdNotHangup(self, fd):
		r = 1
		for i in self.connectors.keys():
			#print "LOOK CONNFD:", fd, "OVER", i, self.connectors[i]["obj"].ReadFDs
			if fd in self.connectors[i]["obj"].ReadFDs:
				s = self.connectors[i]["obj"].IOChannel.cmdrpoll.poll(0)[0][1]
				if s & select.POLLHUP:
					r = 0
					try:
						os.close(fd)
						os.close(self.connectors[i]["obj"].IOChannel.cmd_wfile)
						del self.connectors[i]
					except:
						pass
				else:
					s = self.connectors[i]["obj"].IOChannel.cmdrpoll.poll(0)[0][1]
					if s & select.POLLHUP:
						r = 0
						try:
							os.close(fd)
							os.close(self.connectors[i]["obj"].IOChannel.cmd_rfile)
						except:
							pass
		return r

	def _readFDSet(self):
		ret = []
		for i in self.connectors.keys():
			ret.extend(self.connectors[i]["obj"].ReadFDs)
		return ret

	ReadFDs	= property(_readFDSet, None, None, None)

class Transaction:
	def __init__(self):
		self.sessionData = {}
		self.origin = None	# Connection Info
		self.user = None		# User Info
		self.EOL = 0
		self.TTSID = ""
		self.caller = ""
		self.code = ""
		self.prms = {}
		self.TAState = "NEW"
		self.childTbl = []
		self.TAPID = 0
		self.rfds = []
		self.wfds = []
		self.sendTo = 0
		self.local = 0
		self.handler = None
		self.connection	= None
		self.stage = "UNKNOWN"
		#self.IOChannel = None
		self.cppid = 0
		self.ttskey = ""
		self.retVal = None

	def readConn(self):
		return self.receiveData()

	def receiveData(self):
		global TA_CHLDS
		#TA_CHLDS.sendCommand(self.TAPID, command, PID, TID, data)
		#print "TA READER:", self.TAPID, TA_CHLDS.chlds
		return TA_CHLDS.readConn(self.TAPID)

	def sendCommand(self, command = "", PID = 0, TID = 0, data = None, dTuple = None):
		global TA_CHLDS
		#def	sendCommand(self, child, command, PID = 0, TID = 0, data = None):
		#newTA.sendCommand("TRTU_RUN", chldPID, 0, user.name+"@"+user.realm+newTA.TTSID)
		TA_CHLDS.sendCommand(self.TAPID, command, PID, TID, data, dTuple)

	def fixme(self):
		dbpath = session_path + _makefilename(carrier)
		if not os.path.isdir(dbpath):
			os.mkdir(dbpath)
		dbpath += "/" + _makefilename(source)
		if not os.path.isdir(dbpath):
			os.mkdir(dbpath)
		x = hash(TTSID)
		if x < 0:
			a = "N"
		else:
			a = "P"
		dbpath += "/" + "%s%012x" % (a, abs(x))
		if os.path.isfile(dbpath):
			self.loadSession(dbpath)
		else:
			self.stage = "NEW"

	def addUserData(self, caller, key, value):
		if not self.userData.has_key(caller):
			self.userData[caller] = {}
		self.userData[caller][key] = value

	def getUserData(self, caller, key):
		if not self.userData.has_key(caller):
			return None
		if self.userData[caller].has_key(key):
			return self.userData[caller][key]
		return None

	def delUserData(self, caller, key):
		if not self.userData.has_key(caller):
			return None
		if self.userData[caller].has_key(key):
			del self.userData[caller][key]

	def saveSession(self):
		dom = xml.dom.minidom.getDOMImplementation()
		doc = dom.createDocument(None, "COMARSession", None)
		root = doc.documentElement
		root.appendChild(RPCData._setNode(doc, "SessVersion", "1.0"))
		#root.appendChild(RPCData._setNode(doc, "TTSID", self.TTSID))
		#root.appendChild(RPCData._setNode(doc, "source", self.source))
		#root.appendChild(RPCData._setNode(doc, "stage", self.stage))
		#
		# userData to XML
		#
		udata = doc.createElement("userdata")
		k = self.userData.keys()
		for i in k:
			#print "KEY: ", i, "Value:", self.userData[i]
			tnode = doc.createElement("caller")
			tnode.appendChild(RPCData._setNode(doc, "name", i.__str__()))
			xnode = doc.createElement("savedvalues")
			for j in self.userData[i].keys():
				mnode =	doc.createElement("uservalue")
				mnode.appendChild(RPCData._setNode(doc, "key", j.__str__()))
				vnode = doc.createElement("value")
				COMARValue._dump_value_xml(self.userData[i][j], doc, vnode)
				mnode.appendChild(vnode)
				xnode.appendChild(mnode)
				tnode.appendChild(xnode)
			udata.appendChild(tnode)
		root.appendChild(udata)

		#
		# FIXME: callStack to XML
		#
		txt = doc.toxml()
		doc.unlink()
		fd = open(self.datafile, "w")
		fd.write(txt)
		fd.close()

class TAManager:
	def __init__(self, maxTACount = 48, api_path=""):
		self.TAStack = {}
		self.maxTA = maxTACount
		self.TAPIDIndex = {}
		self.internal = 0
		self.usedTTS = 0
		self.del_que = []
		self.db_ta = gdbm.open(comar_global.comar_tadata + "/tainfo.db", "ws")
		self.db_list = gdbm.open(comar_global.comar_tadata + "/talist.db", "ws")
		self.db_map = gdbm.open(comar_global.comar_tadata + "/tamap.db", "ws")
		if api_path == "":
			api_path = comar_global.comar_modpath+"/ttshandlers"

		dl = dircache.listdir
		is_file = os.path.isfile
		files = dl(api_path)
		sys.path.insert(0, api_path)
		for file in files:
			fname = api_path + "/" + file
			if is_file(fname):
				if file[file.rfind("."):] == ".py":
					mod = self.loadModule(fname)
					if mod:
						for i in mod.HANDLERS.keys():
							self.TAStack[i] = Transaction()
							self.TAStack[i].handler	= mod.HANDLERS[i]()
							#self.TAStack[i].local = True
							mod.createpid = createPID
							mod.createttsid = self.createttsid

		sys.path.pop(0)
		#
		#for old in self.db_list.keys():
		#	self.loadFrom(old)
	def origin(self, xPID):
		key = self.TAPIDIndex[xPID]
		return self.TAStack[key].origin
	def user(self, xPID):
		key = self.TAPIDIndex[xPID]
		return self.TAStack[key].user

	def sendCommand(self, conPID, command="", PID = 0, TID = 0, data = None, dTuple=None):
		key = self.TAPIDIndex[conPID]
		self.TAStack[key].sendCommand(command, PID, TID, data, dTuple)

	def TTSKey(self, xPID):
		key = self.TAPIDIndex[xPID]
		return self.TAStack[key].ttskey

	def mappedTTS(self, key):
		if self.db_map.has_key(key):
			return self.db_map[key]
		return key

	def __destroy__(self):
		self.db_ta.close()

	def loadFrom(self, key):
		pass

	def loadModule(self, module = "", modType="python"):
		""" Load a CAPI Module.. """
		if modType == "python":
			file = os.path.basename(module)
			file = file[:file.rfind('.')]
			mod = __import__(file)
			if "HANDLERS" in dir(mod):
				print "Default TTSID Handler module %s loaded:\n\tProduced TTSID's: %s" % (module, mod.HANDLERS.keys())
				return mod
			del mod # we are not going to use this anymore!
			return None

	def createttsid(self, scope = "HOME"):
		self.usedTTS	+= 1
		return "%s.%08x.%08x.%d" % (scope,os.getpid(), self.usedTTS, time.time())

	def RIP(self, deadChild):
		for key in self.TAStack.keys():
			if self.TAStack[key].TAPID == deadChild:
				print "Child for TA TTSID ", self.TAStack[key].TTSID, "is dead."
				try:
					os.waitpid(self.TAStack[key].cppid, os.WNOHANG)
				except:
					pass
				pos = 0
				dl = -1
				for item in self.del_que:
					if item[0] == key:
						self.endofTA(item[0], item[1])
						dl = pos
						break
					pos += 1
				if dl > -1:
					del self.del_que[pos]					
					print "TA Finished Normally:", item
					del self.TAStack[key]
				else:
					TA_CHLDS.releaseChild(child=deadChild)
					print "TODO: Try for reload transaction: ", self.TAStack[key].TTSID
					del self.TAStack[key]
					#self.loadFrom(key)

	def	ttsid2TA(self, user, ttsid):
		key = self.makettskey(ttsid, user)
		if self.TAStack.has_key(key):
			return self.TAStack[key]
	def endofTA(self, key, value):
		self.db_ta[key+"_st"] = "FINISHED"
		self.db_ta[key+"_value"] = value
		PID = self.TAStack[key].TAPID
		TA_CHLDS.removeChild(PID)
		del self.TAStack[key]
		del self.TAPIDIndex[PID]

	def	create(self, PID, TID, conn, data, user):
		global OM_MGR
		print "TA Create CheckPoint"
		
		rpc = RPCData.RPCStruct()
		rpc.fromString(data)
		key = self.makettskey(rpc.TTSID, user)
		if rpc.Type == "OMCALL":
			omtype = OM_MGR.getOMNodeType(rpc["name"])
			if omtype[1] == "INVALID":
				print "Invalid call:", rpc["name"], omtype
				return None
		elif rpc.Type == "OBJCALL":
			# Only previously registered objects with TA created..
			objtts = self.makettskey(rpc["ttsid"], user)
			objid = rpc["object"].data
			if self.db_ta.has_key(objtts + "_objs"):
				objlst = self.db_ta[objtts + "_objs"].split("\n")
				if not (objid in objlst):
					print "Object '%s' Not found over TTSID: '%s'" % (rpc["ttsid"], objid)
					return None
			else:
				print "No registered TTSID: '%s' for object: '%s'" % (rpc["ttsid"], objid)
				return None
			pass
		#*****************************
		#
		#   WARNING: FIXME !!!!!!!!!!!!!!!!!!!
		#
		#   WE MUST CHECK TTSID AND HOST
		
		chldPID = TA_CHLDS.makeChild()
		print "TA Start Go Fork for accept: ", chldPID
		parentrpid = os.getpid()
		
		pid = os.fork()
		if pid:
			# Parent process
			TA_CHLDS.setIODebug(chldPID, 0, "COMARD/TAROOT:"+rpc.TTSID+"->TANewClient")
			TA_CHLDS.initForParent(chldPID)
			#TA_CHLDS.registerChild(chldPID, TA_CHLDS.myPID)
			#select.select([], [],[], 0.05)   # Wait for 0.1 second..
			newTA = Transaction()
			newTA.origin = conn		# Connection Info
			newTA.user = user		# User Info
			newTA.TTSID = rpc.TTSID
			newTA.EOL = rpc.EOLTime
			newTA.caller = "UI"
			newTA.TAState = "UNKNOWN"
			newTA.TAPID = chldPID
			newTA.rfds = [TA_CHLDS.PID2rfd(chldPID)]
			newTA.wfds = [TA_CHLDS.PID2wfd(chldPID)]
			newTA.stage = "UNKNOWN"
			#newTA.IOChannel = TA_CHLDS.PID2io(chldPID)
			newTA.cppid = pid
			newTA.ttskey = key
			self.TAStack[key] = newTA
			self.TAPIDIndex[chldPID] = key
			print "(%d) NEW TA Job Session Created:%d for %s:%s as %s" % (os.getpid(), pid, user.name+"@"+user.realm, newTA.TTSID, key)
			skey = key

			self.db_list[skey] = user.name+"@"+user.realm+newTA.TTSID
			self.db_ta[skey+"_id"] = rpc.TTSID
			self.db_ta[skey+"_usr"] = user.toString()
			self.db_ta[skey+"_conn"] = conn.toString()
			self.db_ta[skey+"_st"] = "NEW"
			self.db_ta[skey+"_eol"] = str(newTA.EOL)
			self.db_ta[skey+"_rpc"] = data
			self.db_ta[skey+"_call"] = newTA.caller
			self.db_ta[skey+"_objs"] = ""
			return newTA
		else:
			# Child process.
			TA_CHLDS.setIODebug(chldPID, 0, "XTANewClient->COMARD/TAROOT:"+rpc.TTSID)
			gloPIO = TA_CHLDS.PID2io(chldPID)
			gloPPid = TA_CHLDS.myPID + 0
			print "TANewClient IO: child=", chldPID, "glopio=", gloPPid
			new_ph = CHLDHELPER.childHelper(gloPIO, gloPPid, chldPID, "XTANewClient->COMARD/TAROOT:"+rpc.TTSID)
			#new_ph.setIODebug(gloPPid, 0, "TANewClient->COMARD/TAROOT:"+rpc.TTSID)
			new_ph.initForChild(gloPPid)

			new_ph.setIODebug(gloPPid, 0, "XTANewClient->COMARD/TAROOT:"+rpc.TTSID)
			new_ph.parentppid = parentrpid

			cmd = new_ph.waitForParentCmd(2)
			cmd = new_ph.getParentCommand()
			if cmd[2] != "TRTU_RUN":
				print "Job Session TA Provider: Invalid command sequence !"
				new_ph.exit()
			new_ph.useDBSocket()
			OM_MGR.setDBHelper(new_ph)
			jobSession = JOBSESS.jobSessProvider(sessMgr = new_ph, conn = conn, user = user, caller = "UI", key = key)
			print os.getpid(), chldPID, "Register Session:", rpc.TTSID
			if jobSession.register(rpc):
				new_ph.exit()
			jobSession.startTransaction(None)
			#new_ph.sendCommand("TRTU_RUN", chldPID, 0, user.name+"@"+user.realm+"\x00"+newTA.TTSID)
			print "TANewClient", os.getpid(), chldPID, "We are suicide.."
			new_ph.exit()

	def makettskey(self, TTSID, user):
		if self.TAStack.has_key(TTSID):
			# Default TA Key:
			return TTSID
		else:
			if user:
				m = md5.new(user.realm + user.name + TTSID)
			else:
				m = md5.new("comar@localhost" + TTSID)
			return m.hexdigest()

	def status(self, TA):
		if TA.handler:
			rv = TA.handler.status()
		else:
			rv = RPCData.RPCStruct()
			rv.TTSID = self.createttsid(self, scope = "HOME")
			rv.makeRPCData("RESPONSE")
			rv["status"] 		= TA.TAState
			rv["TTSID"]			= TA.TTSID
		return rv

	creators = ( hash("OMCALL"), hash("OBJCALL"), hash("EXEC") )
	notifier = ( hash("NOTIFY"), 0 )
	terminator = ( hash("CANCEL"), 0 )
	queryreq = ( hash("STATUS"), 0 )
	responser = ( hash("RESPONSE"), 0 )
	def _readFDSet(self):
		ret = []
		for i in self.TAStack.keys():
			ret.extend(self.TAStack[i].rfds)
		return ret

	ReadFDs	= property(_readFDSet, None, None)
	def readfd2PID(self, fd):
		#print "Scan For fd:", fd, "over", self.TAStack.keys()
		for i in self.TAStack.keys():
			#print "Scan FD for: %d in %s over %s" % (fd, self.TAStack[i].rfds, i)
			if fd in self.TAStack[i].rfds:
				return self.TAStack[i].TAPID
		return 0

	def fdNotHangup(self, fd):
		r = 1
		for i in self.TAStack.keys():
			print "LOOK TAFD:", fd, "OVER", i, self.TAStack[i].rfds			
			if fd in self.TAStack[i].rfds:
				s = TA_CHLDS.PID2io(self.TAStack[i].TAPID).cmdrpoll.poll(0)[0][1]
				#s = self.TAStack[i].IOChannel.cmdrpoll.poll(0)[0][1]
				#print "TA Checking,",i, s, select.POLLNVAL, select.POLLHUP
				if s & select.POLLNVAL:
					print "TAMGR: IOChannel", TA_CHLDS.PID2io(self.TAStack[i].TAPID).name, "for", self.TAStack[i].TTSID, "is invalid.."
					try:
						
						self.RIP(self.TAStack[i].TAPID)						
						try:
							os.close(fd)
							os.close(self.TAStack[i].IOChannel.cmd_wfile)
						except:
							print "Unable to close channel:", fd, self.ReadFDs
							pass
					except:
						print "Unable to RIP TA:", self.TAStack[i].TAPID
						pass
					
					r = 0
				if s & (select.POLLHUP):
					r = 0
					try:						
						self.RIP(self.TAStack[i].TAPID)
						os.close(fd)
						os.close(self.TAStack[i].IOChannel.cmd_wfile)
						
					except:
						pass
				else:
					#s = self.TAStack[i].IOChannel.cmdrpoll.poll(0)[0][1]
					s = TA_CHLDS.PID2io(self.TAStack[i].TAPID).cmdwpoll.poll(0)[0][1]
					if s & select.POLLHUP:
						r = 0
						try:
							os.close(fd)
							os.close(self.TAStack[i].IOChannel.cmd_rfile)
						except:
							pass
		return r
		
	def readConn(self, xPID):
		for i in self.TAStack.keys():
			if self.TAStack[i].TAPID == xPID:
				#print "Receive from:", i, xPID
				return self.TAStack[i].readConn()

	def commandHandler(self, srcPid, PID, TID, cmd, data, user):
		global TA_CHLDS, CONNS
		clientTA = None
		for i in self.TAStack.keys():
			if self.TAStack[i].TAPID == PID:
				clientTA = i
				break
		if cmd[0] == "S":
			# Session State Commands..
			pass
		elif cmd == "TRSU_DATA": # A TA Data. This is can be a status or response
			rpc = RPCData.RPCStruct()
			rpc.fromString(data)
			key = self.makettskey(rpc.TTSID, user)
			if self.TAStack.has_key(key):
				if self.TAStack[key].local:
					# This is a local TA. We only accept "RESPONSE"
					if rpc.RPCModel() == "local":
						# We must send this data to our local TA.
						pass
				else:
					# This is a "started from remote" TA. We accept "STATUS" or "CANCEL"
					TargetTA = self.TAStack[key]
					if rpc.Type == "CANCEL":
						# A Cancel Request. We send this to
						pass
					else:
						rv = self.status(TargetTA)
						return (PID, TID, "TRTU_SNDR", rv.toString(), user)
			else:
				return (PID, TID, "TNTU_TANF", None, user)
		elif cmd == "TRSU_CKTA":	# Check TA
			# Possible Returns:
			#	TNTU_TANF	NotFound
			#	TRTU_TDA	TAData. Sends TA Status.
			#   TNTU_PTA	Passed TA. Finished, but no timeout.
			key = self.makettskey(data, user)
			if key == None:
				return (PID, TID, "LNTU_KILL", None, user)

			key = self.mappedTTS(key)
			print "seek for :", key, "over",self.TAStack.keys()
			
			if self.TAStack.has_key(key):
				if self.TAStack[key].local:
					return (PID, TID, "TNTU_LOC", None, user)
				else:
					return (PID, TID, "TNTU_ARTA", None, user)
			else:
				key = self.makettskey(data, None)
				key = self.mappedTTS(key)
				if self.TAStack.has_key(key):
					if self.TAStack[key].local:
						return (PID, TID, "TNTU_LOC", None, user)
				return (PID, TID, "TNTU_TANF", None, user)
		elif cmd == "TRSU_RTA":	# Register TA
			# Possible Returns:
			# If this TA is not exists, we create a new TDA
			global CONNS
			print "TA CMD HND: TRSU_RTA Reached"
			conn = CONNS.connInfo(PID, TID)
			if conn != None:
				print "TA CMD HND: Create New TA Entry", os.getpid()				
				new_ta = self.create(PID, TID, conn, data, user)
				print "TA CMD HND: Create New TA Exit", os.getpid()
				if new_ta:
					print "A New TA Created:", os.getpid(), new_ta.TTSID, "PID:", PID
					CONNS.setTAInfo(PID, TID, new_ta.ttskey)
					select.select([],[],[], 0.1)
					new_ta.sendCommand("TRTU_RUN", new_ta.TAPID, 0, user.name+"@"+user.realm+"\x00"+new_ta.TTSID)
					return (PID, TID, "LNSU_MCL", None, user)
				else:
					print "TA Creation denied:"
					return (PID, TID, "LNSU_ERR", None, user)

			return None
		elif cmd == "TRSU_FIN":	# TAFinished
			pass
		elif cmd == "TRSU_TAE":	# FinishTA
			key = self.TAPIDIndex[PID]
			print key, self.TAStack[key].TTSID,":TA Finished with data:", data, type(data)
			if data == 'None':
				#Null Value returned.. 
				retVal = COMARValue.COMARRetVal(1, COMARValue.null_create())				
				print key, self.TAStack[key].TTSID,":TA Finished Null Value:", retVal
				
			x = data.find(" ")
			if x > -1:
				st = int(data[:x].strip())
				vl = data[x:].strip()
				retVal = COMARValue.COMARRetVal(st, COMARValue.load_value_xml(vl))
				print key, self.TAStack[key].TTSID,":TA Finished normally:", retVal
			rpc = RPCData.RPCStruct()
			rpc.TTSID = self.TAStack[key].TTSID
			rpc.makeRPCData("RESPONSE")
			rpc["TTSID"] = self.TAStack[key].TTSID
			rpc["status"] = "RESULT"
			rpc["returnvalue"] = retVal
			res = rpc.xml[:]
			#print "RESULT:", res
			self.del_que.append((key, res))
			return (PID, TID, "TRTU_SNDR", res, user)
		elif cmd == "TRSU_SST":	# SendStatus
			pass
		elif cmd == "TNSU_BRK":	# AbortTA
			pass
		elif cmd == "TNSU_GSID": # Get Local TTSID
			pass
		elif cmd == "TRSU_ACC":	# AcceptResult
			pass
		elif cmd == "TRSU_GET":	# Get Value.
			pass
		elif cmd == "TRSU_SOBJ":  # RegisterObject			
			key = self.TAPIDIndex[srcPid]
			print "Save Object call:", key, srcPid, PID, TID, cmd, data
			objs = self.db_ta[key+"_objs"]
			if len(objs) > 0:
				objs += "\n"
			objs += data
			self.db_ta[key+"_objs"] = objs
			
		elif cmd == "TRSU_RMAP": # RemapTA. CALL->TAM: Şu anki TA'değerini, yeni bir Local TTSID ile map eder. Yeni TTSID'ye gelen istekler doğrudan asıl TA'ya iletilir.
			if clientTA:
				nta = self.createttsid("HOME")
				key = self.makettskey(nta, None)
				self.db_map[key] = self.TAStack[clientTA].TTSID
				return (PID, TID, "TRTU_SSID", nta, user) # NewLocalTTSID
			else:
				return None
		else:
			return None

	def processRPC(self, RPCInfo = None, ConnectInfo = {}):
		rt = hash(RPCInfo.Type)
		print "Processing", RPCInfo.Type
		if rt in self.creators:
			# call create
			pass
		elif rt in self.notifier:
			# call notify
			pass
		elif rt in self.terminator:
			# call CANCEL
			pass
		elif rt in self.queryreq:
			# STATUS call.
			rv = self.status(RPCInfo)
			if type(rv) == type(1):
				return None
			return rv
		elif rt in self.responser:
			pass
		return None


def startDBWorker():
	global TA_CHLDS, root_dbfd
	pio = TA_CHLDS.makeChild()
	pid = os.fork()
	if pid:
		TA_CHLDS.initForParent(pio)
		#TA_CHLDS.registerChild(pio, 0)
		TA_CHLDS.setIODebug(pio, 2, "COMARD->DBWORKER")
		print "DB Thread Child:", pio, TA_CHLDS.PID2io(pio).cmd_rfile, TA_CHLDS.PID2io(pio).cmd_wfile
		root_dbfd = TA_CHLDS.PID2io(pio).cmd_rfile
		return pio
	else:
		TA_CHLDS.initForChild(pio)
		io = TA_CHLDS.PID2io(pio)
		TA_CHLDS.setIODebug(pio, 2, "DBWORKER->COMARD")
		io.debug = 0 #DEBUG_PIPESYNC = 4  DEBUG_INIT	   = 2
		db = DBWORKER.dbWorker(io)
		db.listen()
		print "\n\n\n\nDBWorker Returned.. Bad, very bad !!\n\n\n\n\n\n"
		os._exit(1)

def start():
	"""Starts COMARd"""

	global	CONNS, TA, TA_CHLDS, OM_MGR, DBIO, TIMER, AUTHHELPER, COMARHELPER, DB_THREAD, root_dbfd
	print "Initializing COMARd"
	cont = checkComardPerms()
	if cont == 0:
		print "\n\nSystem permission checks fault..Sorry !!!\nExiting.."
		os._exit(2)
	activeConns = {}
	print "Initialize COMARAPI"
	print "COMAR library directory root:", comar_global.comar_libpath
	print "COMAR module directory root:", comar_global.comar_modpath
	print """
PRE-ALPHA MESSAGE:
\tFor testing COMARd, you must create this directories and
\tcopy/symlink provided default modules.
\tYou can use provided install_comar.py script for this job..
"""
	AUTHHELPER 				= AUTHSYS.authSystem()
	SESSION.root 			= comarRoot()
	COMARHELPER 			= SESSION.root
	CHLDHELPER.root 		= SESSION.root

	COMARAPI.CLASS_CINFO 		= COMARAPI.callerInfoObject
	COMARAPI.CLASS_CHLDHELPER	= CHLDHELPER.childHelper
	COMARAPI.OBJ_COMARValue		= COMARAPI.COMARValue
	COMARAPI.OBJ_HOOKDRV  		= COMARAPI.OBJ_HOOK_DRV()
	COMARAPI.OBJ_IAPI 			= COMARAPI.COMARIAPI()	
	capi = COMARAPI.COMARCAPI()
	capi.init()
	COMARAPI.OBJ_CAPI 			= capi
	CAPI = COMARAPI.COMARAPI()
	#print "CORE API:"
	#for i in dir(CAPI):
	#	print "CORE API:", i, "=", getattr(CAPI, i)
	COMARAPI.API = CAPI

	print "Obj Hooks: provided language modules:"

	for i in CAPI.api_OBJHOOK.Interpreters:
		print "\t%s" % (i)

	initTAMGR()
	#print "COMARAPI::API :"
	#for i in dir(COMARAPI.API):
	#	print i, "=", getattr(COMARAPI.API, i)
	initOM_MGR()
	TIMER = comarTimer()
	DB_THREAD = startDBWorker()
	print "DB_THREAD is", DB_THREAD
	select.select([],[],[], 0.2)
	TA_CHLDS.setDBWorker(DB_THREAD+0)
	

	OM_MGR.setDBHelper(localDBHelper())
	OM_MGR.initOM("COMAR", "OM_XML_CSL", comar_global.comar_om_dtd + "/comar.xml")
	OM_MGR.initOM("CORE", "CORE", comar_global.comar_om_dtd + "/core.xml")
	
	OM_MGR.addObjHandlers(CAPI.api_OBJHOOK)
	
	#OM_MGR.addObjHandlers(objhookClass)
	COMARAPI.OBJ_OMMGR 			= OM_MGR
	CAPI.OMAPI                  = COMARAPI.OBJ_OMMGR
	JOBSESS.OM_MGR = OM_MGR
	JOBSESS.COMARAPI = CAPI

	CONNS = ConnectorModules()
	CONNS.init()
	# PAMmodule.so broken...
	#print "AUTH:", AUTHHELPER.authenticate("PAM", "root", "serdar")
	#print COMARValue.dump_value_xml(capi.call(method = "xini_parse", prms = {"cfgfile":COMARValue.string_create("/etc/X11/XF86Config-4")}, callerInfo = None).returnValue)
	
	if 0:
		print "DIGEST:", AUTHHELPER.digest("HMAC-MD5", "root", "serdar")
		# A Test Code...
		CSL = """method test(x=5,y=10) { test=x+y; }"""
		tmp = OM_MGR.getOMObjList(node = "CORE:eventSys.std.TimerMinutely")
		print "First Real ObjHook List:", tmp
		if tmp:
			for x in tmp:
				hook = OM_MGR.getOMObj(x)
				print "\tHOOK '%s': %s" % (x, hook.__class__)
				runhook = hook[0](OMData = hook[1])
				print "\t\t     Hook require container: ", runhook.useContainer
				print "\t\t Hook persistent capability: ", runhook.canPersist
				runhook.loadInstance(hook[2])
				cv = runhook.runOMNode()
				print "Hook returned:", COMARValue.CVALget(cv)

	print "Connector module pipeset:", CONNS.ReadFDs
	# Fire up COMARd:
	# createLocalTA(node = "CORE:eventSys.std", Type = "method", name="COMARdUp")

	xloop = 450
	while xloop:
		readfds = CONNS.ReadFDs
		TAFDS	= TA.ReadFDs
		if TAFDS:
			#print "TAFDS: ", TAFDS
			readfds.extend(TAFDS)

		DBFD = [ TA_CHLDS.PID2rfd(DB_THREAD) ]
		readfds.extend(DBFD)
		#print "Read FDS:", readfds
		TIMER.checkUp()
		err = []
		try:
			rfds = select.select(readfds, [], [], 10)
		except:
			err = []
			for i in readfds[:]:
				try:
					r = select.select([i], [], [], 0.005)
				except:
					err.append(i)
			rfds = (err, [], [])

		#print "GLOBAL:", readfds, "->", rfds, "TA's:", TAFDS, "DBIO:", DBFD, err
		xloop -= 1
		#print "CH Child Table:", TA_CHLDS.subchlds
		if len(rfds) == 0:
			continue
		for i in rfds[0][:]:
			if i in TAFDS:				
				if TA.fdNotHangup(i):
					conPID = TA.readfd2PID(i)
					acc_data = TA.readConn(conPID)
					print "\n\nA TA Command:", i, conPID, acc_data, "\n\n",
					if acc_data:
						cmd = acc_data[2]
						PID = int(acc_data[0])
						TID = int(acc_data[1])
						data = acc_data[3]
						print "Transaction Command (%s) from PID : %s pkpid:%s cmd:%s" % (i, conPID, PID, cmd), data
						if cmd == "IRSU_APRT":
							print "TAM -- Register Child:", int(data), "->", PID
							TA_CHLDS.registerChild(child=int(data), parent=PID)
						elif cmd == "INSU_PID":
							print "TA New PID Request:", PID #  child, command = "", PID = 0, TID = 0, data = None,
							TA.sendCommand(conPID, "IRTU_PID", PID, TID, "%08d" % createPID())
							print "TA New PID Value Send to:", PID
						elif cmd == "IRSU_DPRT":
							TA_CHLDS.releaseChild(child=int(data))
						elif cmd[0] == "Q":
							#print "TAM: A DB Command:", conPID, PID, TID, cmd, data[:20]
							dcmd = dbIOCmdProc(conPID, PID, TID, cmd, data)
							if dcmd:
								# (PID, TID, CMD, DATA)
								TA.sendCommand(conPID, dTuple = dcmd)
						elif cmd[0] == "T":
							dcmd = TA.commandHandler(conPID, PID, TID, cmd, data, None)
							if dcmd:
								# (PID, TID, CMD, DATA)
								if dcmd[2] == "TRTU_SNDR":
									sendResponse(TA.TTSKey(conPID), TA.origin(conPID), TA.user(conPID), dcmd[3])
								else:
									TA.sendCommand(conPID, dTuple = dcmd)
				else:
					print "We are lost a child (owned channel:%d).. Cry.. :((" % (i)
					conPID = TA.readfd2PID(i)
					TA.RIP(conPID)
			elif i in DBFD:
				acc_data = TA_CHLDS.readConn(DB_THREAD)
				#print "DB FD Active..", acc_data
				io = TA_CHLDS.PID2io(DB_THREAD)
				if io.cmdrpoll.poll(1)[0][1] & select.POLLHUP:
					print DBFD, "DB Worker ölmüş !!"
					os._exit(0)

				if acc_data:
					cmd = acc_data[2]
					PID = int(acc_data[0])
					TID = int(acc_data[1])
					data = acc_data[3]
					#print "DB IOChannel Command (%s) from PID : %s" % (i, cmd)
					if cmd[0] == "Q":
						#print "TAM: A DB Command:", PID, TID, cmd #, data[:20]
						#dcmd = dbIOCmdProc(conPID, PID, TID, cmd, data)
						#if dcmd:
							# (PID, TID, CMD, DATA)
						x = TA_CHLDS.getParentOfChild(PID)
						if x==0: x = PID
						#print "send to ", x, "for ", PID
						#TA_CHLDS.dumpInfo()
						TA_CHLDS.sendCommand(x, cmd, PID, TID, data)
			else:
				conPID = CONNS.readfd2PID(i)
				#print "Connection (%s) from PID : %s" % (i, conPID)
				if CONNS.fdNotHangup(i):
					acc_data = CONNS.readConn(conPID)
					if acc_data:
						# (PID, TID, CMD, DATA)
						#print "Connection data from : %s -> %s" % (conPID, acc_data[2])
						cmd = acc_data[2]
						PID = int(acc_data[0])
						TID = int(acc_data[1])
						data = acc_data[3]
						#print "ROOT * Accepted Data:", cmd, PID, TID,
						if cmd == "IRSU_CONN":
							# A New Call.
							ci = RPCData.connectionInfo(acc_data[3])
							print "Connection from Address	: %s://%s" % (ci.protocol, ci.protoAddr)
							CONNS.sendConn(conPID, "INTU_AUTH", PID, TID)
							print "INTU_AUTH Success."
							CONNS.addConnEntry(PID, TID, conPID, ci, None, None)

						elif cmd == "INSU_CONN":
							print "Temporary Connection: %s://%s"
							CONNS.addConnEntry(PID, TID, conPID, None, None, None)

						elif cmd == "IRSU_APRT":
							TA_CHLDS.registerChild(int(data), PID)
							print "ROOT Add Route:", data, "->", PID

						elif cmd == "IRSU_DPRT":
							TA_CHLDS.releaseChild(int(data))
							print "ROOT Del Route:", data, "->", PID

						elif cmd == "INSU_OFF":
							CONNS.setLinkOffline(PID, TID, 0)

						elif cmd == "INSU_PID":
							print "New PID Request:", PID
							CONNS.sendConn(conPID, "IRTU_PID", PID, TID, "%08d" % createPID())
							print "New PID Value Send to:", PID

						elif cmd == "LNSU_MCL":
							CONNS.sendTarget("LNTU_KILL", PID, TID)

						elif cmd == "IRSU_AUTH":
							user = RPCData.userInfo(acc_data[3])
							print "Auth Info For %d/%d:" % (PID, TID)
							if CONNS.getUser(PID, TID) == None:
								CONNS.sendTarget("INTU_COK", PID, TID)
							CONNS.setUser(PID, TID, user)

						elif cmd in ["IRSU_STD", "IRSU_RTD", "IRSU_PTD"]:
							# SetTASessionData. "<session_id[<=32]> <key[<=32]> <eol> <data[...]>"
							# ReqTASessionData. "<session_id> <key>"
							# PopTASessionData. "<session_id> <key>"
							print "A TA Sess Data Call:", cmd, PID, TID, data
							rcmd = CONNS.sessDataHandler(cmd, PID, TID, data)
							if rcmd != None and rcmd[3] != None:
								print "SDH:", rcmd
								CONNS.sendTarget(rcmd[2], rcmd[0], rcmd[1], rcmd[3])

						elif cmd[0] == "T":
							#print "A TA Command:", acc_data
							user = CONNS.getUser(PID, TID)
							#conn = CONNS.getConn(PID, TID)
							rcmd = TA.commandHandler(conPID, PID, TID, cmd, data, user)
							print "TA Manager Return:", rcmd
							if rcmd:
								CONNS.sendTarget(rcmd[2], rcmd[0], rcmd[1], rcmd[3])
							else:
								CONNS.sendTarget("LNTU_KILL", PID, TID)
							print "Main: Send Complete:", rcmd

						elif cmd[0] == "Q":
							#print "TAM: A DB Command reached:", conPID, PID, TID, cmd, data
							dcmd = dbIOCmdProc(conPID, PID, TID, cmd, data)
							if dcmd:
								# (PID, TID, CMD, DATA)
								TA_CHLDS.sendCommand(conPID, dTuple = dcmd)
					else:
						print "No data readed :("
						os._exit(1)
				else:
					print "We are lost a connector child (owned channel:%d).. Cry.. :((" % (i)


def findopenfile(fileid = ""):
	dl = dircache.listdir("/proc")
	for f in dl:
		if f[0] in "1234567890":
			dn = "/proc/%s/fd/" % (f)
			fdl = dircache.listdir(dn)
			for l in fdl:
				try:
					if os.readlink("%s%s" % (dn,l)) == fileid:
						print "fd Handled on:", f
				except:
					pass


class localDBHelper:
	def dbOpen(self, fileName):
		tid = (len(root_dbs) - 1) + 1
		root_dbs.append(None)
		#findopenfile(os.readlink("/proc/self/fd/%s" % (root_dbfd)))
		#dbIOLocal("QRSU_OPEN", 0, 0, fileName)
		loop = 40
		while loop:
			#print "Wait for DbOpen:", os.readlink("/proc/self/fd/%s" % root_dbfd)
			x = 10
			io = TA_CHLDS.PID2io(DB_THREAD)
			io.debug = 0 #255
			io.name = "DBPIPE"
			io.putCommand("QRSU_OPEN", 0, tid, fileName)
			while x:				
				cx = io.cmdReady()
				if cx == 1:
					break
				elif cx == -1:
					print "EEE DB Pipe Broken :", fileName					
					return 0
				else:
					x -= 1
			if x == 0:
				print "EEE DB Not Ready :", fileName					
				os._exit(1)
				return 0
			#print "IO For dbOpen:", io
			srcpid = 0
			cmd = io.getCommand()
			#print "ROOT DB MGR:", cmd, tid
			if cmd:
				pkPid = int(cmd[0])
				pkTid = int(cmd[1])
				ppid = io.cmd_rfile
				pkData = cmd[3]
				command = cmd[2]
				if pkTid == tid and pkPid == 0 and command == "QRTU_QDB":
					#print "ROOT DB MGR: QRTU_QDB Accepted:", cmd, pkData
					root_dbs[tid] = int(pkData)
					return tid
			else:
				os._exit(1)
			loop -= 1

	def dbClose(self, dbHandle):
		if root_dbs[dbHandle]:
			print "ROOT QRSU_END", 0, 0, root_dbs[dbHandle]
			dbIOLocal("QRSU_END", 0, 0, str(root_dbs[dbHandle]))
			del root_dbs[dbHandle]

	def dbMoveFirst(self, dbHandle, cmd = "QRSU_FRST"):
		dbIOLocal(cmd, 0, 0, self.dbs[dbHandle])
		tid = self.dbWait('QRTU_LOC')
		if tid:
			return tid[1]

	def dbMoveLast(self, dbHandle):
		return self.dbMoveFirst(self, dbHandle, cmd = "QRSU_LAST")

	def dbWrite(self, dbHandle, key, data):
		#print "ROOT DB WRITE:", root_dbs[dbHandle], len(key), key, type(data)
		#print "LOCAL DBWRITE:", dbHandle, type(dbHandle)
		data = "HANDLE=%d\x01KEY=%d %s\x01DATA=%d %s\x01" % (root_dbs[dbHandle], len(key), key, len(data), data)
		#print "QRSU_PUT:", data
		dbIOLocal("QRSU_PUT", 0, 0, data)

	def dbRead(self, dbHandle, key):
		if not root_dbs[dbHandle]:
			print "Invalid DB Handler:", dbHandle
			return None

		#	print "ROOT: GET DB KEY:", dbHandle, self.dbs[dbHandle]
		dbIOLocal("QRSU_GET", 0, 0, "%d %s" % (int(root_dbs[dbHandle]), key))
		tid = self.dbWait('QRTU_DATA')
		if tid:
			return tid[1]

	def dbSeek(self, dbHandle, key):
		dbIOLocal("QRSU_SEEK", 0, 0, "%d %s" % (root_dbs[dbHandle], key))
		tid = self.dbWait('QRTU_LOC')
		if tid:
			return tid[1]

	def dbNext(self, dbHandle, cmd = "QRSU_NEXT"):
		dbIOLocal(cmd, 0, 0, "%d" % (root_dbs[dbHandle], key))
		tid = self.dbWait('QRTU_LOC')
		return tid

	def dbPrev(self, dbHandle):
		return self.dbNext(dbHandle, cmd = "QRSU_PREV")
		pass

	def dbWait(self, waitcmd, loop = 40):
		global DB_THREAD, root_dbfd
		while loop:
			rds = select.select([root_dbfd], [], [], 1)
			if len(rds[0]) == 0:
				return 0
			rfd = rds[0][0]
			io = TA_CHLDS.PID2io(DB_THREAD)
			#print "IO For dbMF:", io
			srcpid = 0
			ppid = io.cmd_rfile
			cmd = io.getCommand()
			pkPid = int(cmd[0])
			pkTid = int(cmd[1])
			pkData = cmd[3]
			command = cmd[2]
			#print "LOCAL dbWait: %s %s '%s'='%s' '%s' %s'" % (rds, root_dbfd, command, cmd, pkPid, pkTid)
			
			if pkTid == 0 and pkPid == 0 and command == waitcmd:
				#PID, TID, CMD, DATA
				#print "RESPONSE:", pkData
				tid = SESSION.root.db10tuple(pkData)
				return tid
			loop -= 1

def dbIOLocal(cmd = "", PID = 0, TID = 0, data = None):
	global DB_THREAD
	#print "TAM LOCAL DB SENDER:", PID, TID, cmd, type(data), "-->", DB_THREAD
	TA_CHLDS.sendCommand(child = DB_THREAD + 0, command = cmd, PID = 0, TID = 0, data = data)

def dbIOCmdProc(conPID, PID, TID, cmd, data):
	global DB_THREAD
	#print "TAM DB SENDER:", conPID, PID, TID, cmd, type(data), "-->", DB_THREAD
	TA_CHLDS.sendCommand(child = DB_THREAD + 0, command = cmd, PID = PID, TID = TID, data = data)


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

def sendResponse(ttskey = None, connInfo = None, user=None, rpcXml = None):
	global CONNS
	print "Response for TTSKEY:", ttskey
	#print "Send Response To:", connInfo.toString()
	#print "Result send user:", user.toString()
	#print "Response Data:", rpcXml
	rpc = RPCData.RPCStruct(xmlData = rpcXml)
	online = CONNS.getTAConn(ttskey)
	print "ONLINE:", online
	if online:
		# (self.activeConns[pi][0], PID, TID)
		s = rpc.toString()
		#print "TRTU_SNDR", s
		#ConnPID, command, PID = 0, TID = 0, data = None
		CONNS.sendConn(online[0], "TRTU_SNDR", online[1], online[2], s)

# comarTimer. Provides a one minute resolution timer.

class comarTimer:
	def __init__(self):
		self.eventdb	= bsddb.btopen(comar_global.comar_basic_data + "/timer_queue.db", "w")
		self.cache		= {}
		self.minutes	= [0, 30]
		self.hours		= [0]
		self.lastDay	= 0
		self.lastMinute = -1
		self.lastHour   = -1
		self.morning	= 6 * 60
		self.wstart		= 8 * 60
		self.wstop		= 17 * 60
		self.periodicals = []
	def addItem(self, evstring = ""):
		pass
	def addOMNode(self, node = "", method="", period=""):
		pass
	def addItem(self, evstring = ""):
		pass
	def addPeriodCall(self, func):
		self.periodicals.append(func)
	def delPeriodCall(self, func):
		p = 0
		for i in self.periodicals:
			if i == func:
				del self.periodicals[p]
				return
			p += 1
	def checkUp(self):
		for f in self.periodicals:
			f()
		minute = int(time.strftime("%M"))
		hour   = int(time.strftime("%H"))
		if minute != self.lastMinute:
			if self.lastMinute == -1:
				self.lastMinute = minute
				self.lastHour   = hour
				#self.eventdb.seek()
				return
			self.lastMinute = minute
			#print "Minute period events fired !!!"
			current = hour * 60 + minute
			if minute in self.minutes:
				print "A minute event captured"
				if hour in self.hours:
					print "A Hourly event captured"
			if self.morning == current:
				print "Good Morning.."
			else:
				if self.wstart == current:
					print "Workday started !"
				elif self.wstop == current:
					print "Workday finished !"
			tim = time.strftime("%Y%m%d%H%M")
			if self.eventdb.has_key(tim):
				print "A scheduled event occurred:", tim
				del self.eventdb[tim]
		else:
			return

# Event Subsystem

class comarEvent:
	def __init__(self):
		global TIMER, FILEMON, PROCMON
		self.eventdb = bsddb.btopen(comar_global.comar_basic_data + "/event_queue.db", "w")
		self.eviddb = bsddb.btopen(comar_global.comar_basic_data + "/event_ids.db", "w")
		self.remotes = bsddb.btopen(comar_global.comar_basic_data + "/event_remote.db", "w")
		self.evstart = time.time()
		self.lastev  = 0
		self.providers = { "TIMER": TIMER, "FMON":FILEMON, "PMON":PROCMON }
		
	def addObj(self, eventid = "", wait=0, objdesc = "", method = ""):
		evclass = eventid.split(":")[0]
		evtype = eventid.split(":")[1]
		if evclass == "STD-EVENT":
			if self.providers.has_key(evtype):
				self.providers[evtype].addItem(eventid)
		if wait != 0:
			wait = 1
		if self.eviddb.has_key(eventid):
			evntnum = int(self.eviddb[eventid]) + 1
		else:
			evntnum = 0
		self.eviddb[eventid] = str(evntnum)
		taskKey = "%s_%8x" % (eventid, evntnum)
		self.eventdb[taskKey] = "O %s %s %s" % (wait, objdesc, method)
		return taskKey

	def addNode(self, eventid = "", wait=0, node = ""):
		evclass = eventid.split(":")[0]
		evtype = eventid.split(":")[1]
		if evclass == "STD-EVENT":
			if self.providers.has_key(evtype):
				self.providers[evtype].addItem(eventid)
		if wait != 0:
			wait = 1
		if self.eviddb.has_key(eventid):
			evntnum = int(self.eviddb[eventid]) + 1
		else:
			taskKey = "%s_%8x" % (eventid, 0)
			self.eventdb[taskKey] = "INX"
			evntnum = 1
		self.eviddb[eventid] = str(evntnum)
		taskKey = "%s_%8x" % (eventid, evntnum)
		self.eventdb[taskKey] = "N %s %s" % (wait, node)
		return taskKey

	def addNotify(self, eventid = "", remote = ""):
		evclass = eventid.split(":")[0]
		evtype = eventid.split(":")[1]
		if evclass == "STD-EVENT":
			if self.providers.has_key(evtype):
				self.providers[evtype].addItem(eventid)
		if wait != 0:
			wait = 1
		if self.eviddb.has_key(eventid):
			evntnum = int(self.eviddb[eventid]) + 1
		else:
			taskKey = "%s_%8x" % (eventid, 0)
			self.eventdb[taskKey] = "INX"
			evntnum = 1
		self.eviddb[eventid] = str(evntnum)
		taskKey = "%s_%8x" % (eventid, evntnum)
		self.eventdb[taskKey] = "R %s %s" % (wait, remote)
		return taskKey

	def delete(self, taskKey = ""):
		if self.eventdb.has_key(taskKey):
			del self.eventdb[taskKey]

	def delEvent(self, eventid = ""):
		if self.eviddb.has_key(eventid):
			col = []
			tp = self.eventdb.set_location("%s_%8x" % (eventid, 0))
			while tp:
				key = tp[0]
				if key[0:key.rfind("_")] != eventid:
					break
				col.append(key[-8:])
				try:
					tp = self.eventdb.next()
				except:
					tp = None
			for i in col:
				del self.eventdb["%s_%s" % (eventid, i)]
			del self.eviddb[eventid]
			evclass = eventid.split(":")[0]
			evtype = eventid.split(":")[1]
			if evclass == "STD-EVENT":
				if self.providers.has_key(evtype):
					self.providers[evtype].delItem(eventid)

	def fireUp(self, eventid = ""):
		if self.eviddb.has_key(eventid):
			tp = self.eventdb.set_location("%s_%8x" % (eventid, 0))
			while tp:
				key = tp[0]
				if key[0:key.rfind("_")] != eventid:
					break
				evcls = tp[1][0]
				if evcls == "R":
					print "EVSYS: Remote Notify:", tp[1]
				elif evcls == "O":
					print "EVSYS: Object Fired:", tp[1]
				elif evcls == "N":
					print "EVSYS: OM NODE Fired:", tp[1]
				try:
					tp = self.eventdb.next()
				except:
					tp = None

	def getNewEventId(self, ev_class = ""):
		self.lastev += 1
		return "USER:%s:%f:%f" % (ev_class, self.evstart, self.lastev)

	def cmdHandler(self, PID, TID, command, data):
		if command == "ERSU_NID": 		#newEventId. ANY->TAMEV:DATA = Event Class.
			if data == None:
				data == "USER"
			eid = self.getNewEventId(data)
			return (PID, TID, "ERTU_NID", eid)
		elif command == "ERSU_AOBJ": 	#addNewEventObject. ANY->TAMEV: DATA = EVENTID=eventid\x00OBJECT=objDescriptor\x00METHOD=methodName\x00WAIT=0\x00
			d = stio2dict(data)
			if d != None and len(d) > 0:
				tk = self.addObj(d["EVENTID"], int(d["WAIT"]), d["OBJECT"], d["METHOD"])
			return (PID, TID, "ERTU_NTK", tk)
		elif command == "ERSU_AOM": 	#addNewEventOMNode. ANY->TAMEV: DATA = EVENTID=eventid\x00NODE=OMNode\x00WAIT=0\x00
			d = stio2dict(data)
			if d != None and len(d) > 0:
				tk = self.addNode(d["EVENTID"], int(d["WAIT"]), d["NODE"])
			return (PID, TID, "ERTU_NTK", tk)
		elif command == "ERSU_DTK": 	#deleteEventTask. ANY->TAMEV: DATA = taskKey
			if data == None:
				return None
			self.delete(data)
			return None
		elif command == "ERSU_FUP": 	#FireEvent. ANY->TAMEV: DATA = eventid.
			if data == None:
				return None
			self.fireUp(data)
			return None

class comarRoot:
	def __init__(self):
		self.createPID = createPID
		self.db10tuple = DBWORKER.db10tuple
		self.stio2dict = stio2dict
		self.OM_MGR	   = OM_MGR
		self.authhelper= AUTHHELPER
		self.preferences = { "auth":{"pwdcheck":"SYSTEM"}}

def checkComardPerms():
	global	CONNS, TA, TA_CHLDS, OM_MGR, DBIO, TIMER, AUTHHELPER, COMARHELPER
	if os.getuid():
		print "Only root can be use this program\nExiting.."
		os._exit(1)
	datadir_stat = os.stat_result(os.stat(comar_global.comar_data))
	libdir_stat = os.stat_result(os.stat(comar_global.comar_libpath))
	cont = 1
	if datadir_stat.st_uid != 0:
		print "\n\nSECURITY ERROR !!!\nCOMAR Data Dir. '%s' must be owned 'root'.\n\tBut it's owned by '%s'" % (comar_global.comar_data,
			pwd.getpwuid(datadir_stat.st_uid)[0])
		cont = 0
	if (datadir_stat.st_mode & 511) != 0700:
		print "\n\nSECURITY ERROR !!!\nCOMAR Data Dir. '%s' permissions must be 0700\n\tbut its mode 0%o" % (comar_global.comar_data,
			datadir_stat.st_mode & 511)
		cont = 0
	if libdir_stat.st_uid != 0:
		print "\n\nSECURITY ERROR !!!\nCOMAR Library Dir. '%s' must be owned 'root'.\n\tBut it's owned by '%s'" % (comar_global.comar_libpath,
				pwd.getpwuid(libdir_stat.st_uid)[0])
		cont = 0
	if (libdir_stat.st_mode & 511) != 0700:
		print "\n\nSECURITY ERROR !!!\nCOMAR Library Dir. '%s' permissions must be 0700\n\tbut its mode 0%o" % (comar_global.comar_libpath,
				libdir_stat.st_mode & 511)
		cont = 0
	return cont

if __name__ == "__main__":
	#stdf = open("dbgfile", "w")
	#sys.stdout.close()	
	#f = os.dup(stdf.fileno())
	#sys.stdout = stdf
	start()
