#!/usr/bin/python
# -*- coding: utf-8 -*-
# TACALL	- JOB/CALL/EXEC Session Provider.
# Copyright (c) 2003-2005 TUBITAK-UEKAE. All Rights Reserved.

# standart python modules
import os
import sys
import select
import copy
import cPickle
import gdbm

# COMAR modules
import comar_global
import CHLDHELPER

COMARAPI = None
OM_MGR = None

class TAcallSession:
	def __init__(self, sessMgr = None, seq_key = "", parent_seq = "", Type = "", Name = "", prms = {}, conn=None, user=None, value = None, caller=""):
		self.container = None
		self.c_type = Type
		self.c_name = Name
		self.c_prms = prms
		self.c_value = value
		#self.callerInfo	= callerInfo
		self.procHelper	= sessMgr
		self.callerInfo	= None
		self.pre_last = ""	# if "" -> first element, if -> None all elements passed.
		self.post_last = ""
		self.seq_key = seq_key
		self.parent_seq = parent_seq
		self.child_seq = ""
		self.mode  = ""
		self.runit = None
		self.conn  = conn
		self.user  = user
		self.caller = caller
		self.retVal = {}
		self.waitFor = {}

	def initOMCALL(self, Node=""):
		self.mode = "OMCALL"
		self.runit = Node
		omattrs = OM_MGR.getOMProperties(self.runit)
		if omattrs == None:
			print "TACALL Init:Invalid call:", self.runit
			return 1

	def initOBJCALL(self, ObjId=""):
		self.mode = "OBJCALL"
		self.runit = ObjId
	def initEXEC(self, Code="", Lang=""):
		self.mode = "EXEC"
		self.runit = Lang + ":" + Code

	def execute(self):
		print "\n\nEXECUTE STARTED\n\n", OM_MGR, OM_MGR.dbhelper, OM_MGR.dbhelper.dbSocket, "PRMS:", self.c_prms
		if self.mode == "OMCALL":
			omattrs = OM_MGR.getOMProperties(self.runit)
			if omattrs == None:
				print "TACALL EXECUTE: Invalid call:", self.runit
				self.procHelper.exit()
			acl_check = OM_MGR.checkAccess(self.callerInfo, self.runit)
			if "usecontainer" in omattrs:
				print "Exec Session: Require a container.."
				objs = OM_MGR.getOMObjList( node = self.runit )
				print "Exec Container ObjList:", objs
				retStack = {}
				rv = "1 <null/>"
				for key in objs:
					hook = OM_MGR.getOMObj(key)
					print "\tHOOK '%s': %s :" % (self.runit, hook.__class__), hook
					ci = OM_MGR.getCInfo(self.runit, key, self.user, self.conn, self.caller)
					#print "OM MGRS CALLERINFO", ci
					if "multicall" in omattrs:
						ret = self.executeOne(key, hook, ci, self.c_name, self.c_type, self.c_prms)
						print "HOOK ITEM ADD:", ret
						retStack[ret["PID"]] = ret["key"]
						cont = 1
						save = self.procHelper.cmdHandler
					else:
						runhook = hook[0](cAPI=ci[0], callerInfo=ci[1], chldHelper = self.procHelper, OMData = hook[1])
						runhook.loadInstance(hook[2])
						#def runOMNode(self, prms = {}, Type = "", name = "" ):
						cn = self.c_name[self.c_name.rfind(".")+1:]
						cv = runhook.runOMNode(prms=self.c_prms, Type = self.c_type, name = cn)
						#print os.getpid(), "Hook returned:", cv.execResult, COMARAPI.OBJ_COMARValue.CVALget(cv.returnValue)
						if cv.execResult == 0:
							rv = "%d %s" % (cv.execResult, COMARAPI.COMARValue.dump_value_xml(cv.returnValue))
							break
				if "multicall" in omattrs:
					cont = 1
					self.waitFor = retStack
					self.procHelper.addSessionCommand([ "TRSU_FIN", "TNSU_GET", "TNSU_GSID", "LNTU_KILL" ])
					self.procHelper.cmdHandler = self.execCmdHandler
					usepid = self.procHelper.myPID
					for i in retStack.keys():
						print "START ITEM:", i
						#self.procHelper.registerChild(i, self.procHelper.myPID)
						self.procHelper.sendCommand(child = i, command = "TNTU_EXEC", PID = usepid, TID = 0, data = None)
					while cont:
						pv = self.procHelper.ProcessIO()
						print "A Call Captured ?", pv
						if len(self.waitFor) == 0:
							break
						if pv == -2:
							cont = 0
					#print "\tCollected retvals:", self.retVal
					rx = None
					if len(self.retVal.keys()) > 1:
						rx = COMARAPI.COMARValue.array_create()
						rc = 0
						for i in self.retVal.keys():
							s = self.retVal[i]
							x = s.find(" ")
							stat = int(s[:x])
							if stat == 0:
								res = s[x+1:]
								val = COMARAPI.COMARValue.load_value_xml(res)
								COMARAPI.COMARValue.array_additem(rx, str(rc), 0, val)
								rc += 1
					else:
						s = self.retVal[self.retVal.keys()[0]]
						x = s.find(" ")
						stat = int(s[:x])
						if stat == 0:
							res = s[x+1:]
							rx = COMARAPI.COMARValue.load_value_xml(res)
					if rx:
						rv = "0 %s" % COMARAPI.COMARValue.dump_value_xml(rx)
				return rv
			else:
				objs = OM_MGR.getOMObjList( node = self.runit )
				key = objs[0]
				ci = OM_MGR.getCInfo(self.runit, key, self.user, self.conn, self.caller)
				hook = OM_MGR.getOMObj(self.runit)
				runhook = hook[0](cAPI=ci[0], callerInfo=ci[1], chldHelper = self.procHelper, OMData = hook[1])
				runhook.loadInstance(hook[2])
				cv = runhook.runOMNode(self.c_prms)
				print os.getpid(), "Oneshot Hook returned:", cv.execResult, COMARAPI.COMARValue.CVALget(cv.returnValue)
				rv = "%d %s" % (cv.execResult, COMARAPI.COMARValue.dump_value_xml(cv.returnValue))
				return rv

		elif self.mode == "OBJCALL":
			pass
		elif self.mode == "EXEC":
			#hook = OM_MGR.
			pass

	def execCmdHandler(self, From, srcpid, ppid, rfd, pkPid, pkTid, command, pkData):
		print self.procHelper.myPID, "A exec session cmd captured:", From, srcpid, ppid, rfd, pkPid, pkTid, command #, pkData
		if command == "TRSU_FIN":
			print os.getpid(), self.procHelper.myPID, "A TRSU FIN Captured (ExecSession/ExecCmdHandler):", From, srcpid, ppid, rfd, pkPid, pkTid, command #, pkData
			self.procHelper.sendCommand(int(srcpid), "LNTU_KILL", pkPid, pkTid, pkData)
			if pkPid in self.waitFor.keys():
				self.retVal[pkPid] = pkData
				del self.waitFor[pkPid]
			else:
				self.procHelper.sendParentCommand(command, pkPid, pkTid, pkData)
				#pass
		elif command == "TRTU_TAE":
			print self.procHelper.myPID, "A TRTU TAE Captured (ExecSession/ExecCmdHandler):", From, srcpid, ppid, rfd, pkPid, pkTid, command #, pkData
			self.procHelper.sendCommand(pkPid, command, pkPid, pkTid, pkData)
		elif command == "TRSU_OMC":
			self.procHelper.sendParentCommand(command, pkPid, pkTid, pkData)
		elif command == "LNTU_KILL":
			self.procHelper.exit()

	def executeOne(self, key, hook, ci, name, Type, prms):
		" Execute post/pre/hook script."
		global OM_MGR
		chldPID = self.procHelper.makeChild()
		parentrpid = os.getpid()
		print "Executing With Container..", chldPID, self.mode, self.runit, prms
		pid = os.fork()
		if pid:
			self.procHelper.initForParent(chldPID)
			#self.procHelper.registerChild(chldPID, self.procHelper.myPID)
			self.procHelper.setIODebug(chldPID, 0, "TASession->ExecSession")
			return { "PID":chldPID, "key":key }
		else:
			# Child..
			gloPIO = self.procHelper.PID2io(chldPID)
			gloPPid = self.procHelper.myPID + 0
			new_ph = CHLDHELPER.childHelper(gloPIO, gloPPid, chldPID, "ExecSession->TASession(x1)")			
			new_ph.parentppid = parentrpid
			new_ph.initForChild(gloPPid)
			new_ph.setIODebug(gloPPid, 0, "ExecSession->TASession(X2)")
			new_ph.modName = "ExecSession->TASession(X3)"
			new_ph.waitForParentCmd(1)
			new_ph.useDBSocket()

			while 1:
				if new_ph.waitForParentCmd(timeout = 2):
					break

			cmd = new_ph.getParentCommand()
			print "XXXXXXXXXXXX Exec Session Child: ", new_ph.myPID, os.getpid(), chldPID, new_ph.myPID, new_ph.gloPPid, cmd, "PRMS:", prms
			runhook = hook[0](cAPI=ci[0], callerInfo=ci[1], chldHelper = new_ph, OMData = hook[1])
			runhook.loadInstance(hook[2])
			#def runOMNode(self, prms = {}, Type = "", name = "" ):
			cn = name[name.rfind(".")+1:]
			cv = runhook.runOMNode(prms=prms, Type = Type, name = cn)
			print os.getpid(), "Hook returned:", cv.execResult, COMARAPI.COMARValue.CVALget(cv.returnValue)
			rv = "%d %s" % (cv.execResult, COMARAPI.COMARValue.dump_value_xml(cv.returnValue))
			new_ph.sendParentCommand("TRSU_FIN", new_ph.myPID, 0, rv)

			while 1:
				print "Wait for parent LNTU_KILL"
				if new_ph.waitForParentCmd(timeout = 2):
					cmd = new_ph.getParentCommand()
					print cmd
					if cmd[2] == "LNTU_KILL":
						break

			new_ph.exit()

api_COMARAPI = None
api_CAPI = None
api_COMARValue = None
