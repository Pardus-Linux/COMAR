#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2004, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.

# TACALL.py
# JOB/CALL/EXEC Session Provider.

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
		self.c_object = None
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
		self.objindex = ""
		
	def initINXOM(self, node="", inx = ""):
		self.mode = "INDEXEDOM"
		self.runit = node
		self.objindex = inx
		
	def initOMCALL(self, Node=""):
		self.mode = "OMCALL"
		self.runit = Node
		omattrs = OM_MGR.getOMProperties(self.runit)
		if omattrs == None:
			print "TACALL Init:Invalid call:", self.runit
			return 1

	def initOBJCALL(self, Obj=None, ObjMethod=""):
		self.mode = "OBJCALL"
		self.runit = ObjMethod
		self.c_object = Obj
		print "OBJECT CALL:", Obj, ObjMethod
		
	def initEXEC(self, Code="", Lang=""):
		self.mode = "EXEC"
		self.runit = Lang + ":" + Code

	def execute(self):
		print "TACALL.execute: EXECUTE STARTED", OM_MGR, OM_MGR.dbhelper, OM_MGR.dbhelper.dbSocket, "PRMS:", self.c_prms
		if self.mode == "OBJCALL":
			print "Execute ObjCall:", self.c_object.data, self.runit, self.c_prms,
			objkeys = OM_MGR.getOBJList(self.c_object)			
			#print objkeys
			for objkey in objkeys:
				hnd = OM_MGR.getOBJHandler(objkey)
				print "Return hook:", hnd
				retStack = {}
				rv = "1 <null/>"
				retobj = COMARAPI.COMARValue.COMARValue(type=object, data="")
				hook = hnd[2]
				ci = hnd[1]
				print "\tOBJCALL HOOK '%s': %s :" % (self.runit, hook.__class__), hook, ci.omkey, hook[2]
				ret = self.executeOne(ci.omkey, hook, hnd, self.c_name, self.c_type, self.c_prms)
				print "OBJCALL HOOK ITEM ADD:", ret
				retStack[ret["PID"]] = ret["key"]
				
			save = self.procHelper.cmdHandler			
			cont = 1
			self.waitFor = retStack
			self.procHelper.addSessionCommand([ "TRSU_FIN", "TNSU_GET", "TNSU_GSID", "LNTU_KILL", "TRSU_SOBJ" ])
			self.procHelper.cmdHandler = self.execCmdHandler
			usepid = self.procHelper.myPID
			for i in retStack.keys():
				print "START OBJCALL ITEM:", i
				#self.procHelper.registerChild(i, self.procHelper.myPID)
				self.procHelper.sendCommand(child = i, command = "TNTU_EXEC", PID = usepid, TID = 0, data = None)
			while cont:
				pv = self.procHelper.ProcessIO()
				print "A OBJCALL Call Captured ?", pv
				if len(self.waitFor) == 0:
					break
				if pv == -2:
					cont = 0
			#print "\tCollected retvals:", self.retVal
			rx = None					
			retobj = COMARAPI.COMARValue.COMARValue(type="object", data="")
			if len(self.retVal.keys()) > 1:						
				rc = 0
				for i in self.retVal.keys():
					s = self.retVal[i]
					x = s.find(" ")
					stat = int(s[:x])
					if stat == 0:
						res = s[x+1:]
						val = COMARAPI.COMARValue.load_value_xml(res)
						if val.type == "object":
							retobj = OM_MGR.objectMerge(retobj, val)									
						else:
							if rx == None:
								rx = COMARAPI.COMARValue.array_create()
							COMARAPI.COMARValue.array_additem(rx, str(rc), 0, val)
							
						rc += 1				
			else:
				s = self.retVal[self.retVal.keys()[0]]
				x = s.find(" ")
				stat = int(s[:x])						
				if stat == 0:
					res = s[x+1:]
					print "TACALL RES BUILDER ADD: ", res, type(res)
					if res != 'None':							
						val = COMARAPI.COMARValue.load_value_xml(res)
						if val.type == "object":
							retobj = val
						else:
							rx = val
			if rx or len(retobj.data) > 0:						
				if len(retobj.data) > 0:
					if rx:
						print "WARNING: Mixing of Object/Data retvals. Data retvals ignored !"							
					rv = "0 %s" % COMARAPI.COMARValue.dump_value_xml(retobj)
				else:
					rv = "0 %s" % COMARAPI.COMARValue.dump_value_xml(rx)
			else:
				rv = "0 %s" % COMARAPI.COMARValue.dump_value_xml(COMARAPI.COMARValue.null_create())
			return rv				
		elif self.mode == "INDEXEDOM":
			return "1 <null/>"
		elif self.mode == "OMCALL":
			omtype = OM_MGR.getOMNodeType(self.runit)
			if (omtype[0] == 1 and omtype[1] != "INVALID") or (omtype[1] == "OBJECT"):
				# indexed OMCALL
				print "Indexed OMCALL:", self.runit, self.c_prms, omtype
				# omtype: (1, "OBJECT", nname, None, inxpart)
				if omtype[1] == "OBJECT" and omtype[0] == 0:
					rx = COMARAPI.COMARValue.array_create()
					objs = OM_MGR.objectGetList(self.runit)					
					print "objs:", objs
					rc = 0
					for i in objs:						
						COMARAPI.COMARValue.array_additem(rx, str(rc), 0, COMARAPI.COMARValue.string_create(i))
						rc += 1
					return "0 %s" % COMARAPI.COMARValue.dump_value_xml(rx)
				elif omtype[1] == "OBJECT" and omtype[0] == 1:
					objkey = OM_MGR.objectGetImmediate(omtype[2], omtype[4])
					print "IMMEDIATE OBJECT:", objkey
					rx = COMARAPI.COMARValue.COMARValue(type="object", data=objkey)
					return "0 %s" % COMARAPI.COMARValue.dump_value_xml(rx)					
				else:
					objkey = OM_MGR.objectGetImmediate(omtype[2], omtype[4])
				
				
				hnd = OM_MGR.getOBJHandler(objkey)
				print "Return hook:", hnd
				retStack = {}
				rv = "1 <null/>"
				retobj = COMARAPI.COMARValue.COMARValue(type=object, data="")
				hook = hnd[2]
				ci = hnd[1]
				print "\tINDEXE OBJCALL HOOK '%s': %s :" % (self.runit, hook.__class__), hook, ci.omkey, hook[2]
				ret = self.executeOne(ci.omkey, hook, hnd, self.c_name, self.c_type, self.c_prms)
				print "INDEXED HOOK ITEM ADD:", ret
				retStack[ret["PID"]] = ret["key"]
				
				save = self.procHelper.cmdHandler	
				cont = 1
				self.waitFor = retStack
				self.procHelper.addSessionCommand([ "TRSU_FIN", "TNSU_GET", "TNSU_GSID", "LNTU_KILL", "TRSU_SOBJ" ])
				self.procHelper.cmdHandler = self.execCmdHandler
				usepid = self.procHelper.myPID
				for i in retStack.keys():
					print "START OBJCALL ITEM:", i
					#self.procHelper.registerChild(i, self.procHelper.myPID)
					self.procHelper.sendCommand(child = i, command = "TNTU_EXEC", PID = usepid, TID = 0, data = None)
				while cont:
					pv = self.procHelper.ProcessIO()
					print "A OBJCALL Call Captured ?", pv
					if len(self.waitFor) == 0:
						break
					if pv == -2:
						cont = 0
				#print "\tCollected retvals:", self.retVal
				rx = None					
				retobj = COMARAPI.COMARValue.COMARValue(type="object", data="")
				if len(self.retVal.keys()) > 1:						
					rc = 0
					for i in self.retVal.keys():
						s = self.retVal[i]
						x = s.find(" ")
						stat = int(s[:x])
						if stat == 0:
							res = s[x+1:]
							val = COMARAPI.COMARValue.load_value_xml(res)
							if val.type == "object":
								retobj = OM_MGR.objectMerge(retobj, val)									
							else:
								if rx == None:
									rx = COMARAPI.COMARValue.array_create()
								COMARAPI.COMARValue.array_additem(rx, str(rc), 0, val)
								
							rc += 1				
				else:
					s = self.retVal[self.retVal.keys()[0]]
					x = s.find(" ")
					stat = int(s[:x])						
					if stat == 0:
						res = s[x+1:]
						print "TACALL RES BUILDER ADD: ", res, type(res)
						if res != 'None':							
							val = COMARAPI.COMARValue.load_value_xml(res)
							if val.type == "object":
								retobj = val
							else:
								rx = val
				if rx or len(retobj.data) > 0:						
					if len(retobj.data) > 0:
						if rx:
							print "WARNING: Mixing of Object/Data retvals. Data retvals ignored !"							
						rv = "0 %s" % COMARAPI.COMARValue.dump_value_xml(retobj)
					else:
						rv = "0 %s" % COMARAPI.COMARValue.dump_value_xml(rx)
				else:
					rv = "0 %s" % COMARAPI.COMARValue.dump_value_xml(COMARAPI.COMARValue.null_create())
				return rv	

			omattrs = OM_MGR.getOMProperties(self.runit)
			
			if omattrs == None:
				print "TACALL EXECUTE OMCALL: Invalid call:", self.runit
				return "1 <null/>"					
			acl_check = OM_MGR.checkAccess(self.callerInfo, self.runit)
			if "usecontainer" in omattrs:
				print "Exec Session: Require a container.."
				objs = OM_MGR.getOMObjList( node = self.runit )
				print "Exec Container ObjList:", objs
				retStack = {}
				rv = "1 <null/>"
				retobj = COMARAPI.COMARValue.COMARValue(type=object, data="")				
				for key in objs:
					hook = OM_MGR.getOMObj(key)
					print "\tHOOK '%s': %s :" % (self.runit, hook.__class__), hook, key
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
							if cv.returnValue.type == "object":
								retobj = OM_MGR.objectMerge(retobj, cv.returnValue)
							else:
								rv = "%d %s" % (cv.execResult, COMARAPI.COMARValue.dump_value_xml(cv.returnValue))
							break
				if "multicall" in omattrs:
					cont = 1
					self.waitFor = retStack
					self.procHelper.addSessionCommand([ "TRSU_FIN", "TNSU_GET", "TNSU_GSID", "LNTU_KILL", "TRSU_SOBJ" ])
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
					retobj = COMARAPI.COMARValue.COMARValue(type="object", data="")
					if len(self.retVal.keys()) > 1:						
						rc = 0
						for i in self.retVal.keys():
							s = self.retVal[i]
							x = s.find(" ")
							stat = int(s[:x])
							if stat == 0:
								res = s[x+1:]
								val = COMARAPI.COMARValue.load_value_xml(res)
								if val.type == "object":
									retobj = OM_MGR.objectMerge(retobj, val)									
								else:
									if rx == None:
										rx = COMARAPI.COMARValue.array_create()
									COMARAPI.COMARValue.array_additem(rx, str(rc), 0, val)
									
								rc += 1
						
					else:
						s = self.retVal[self.retVal.keys()[0]]
						x = s.find(" ")
						stat = int(s[:x])						
						if stat == 0:
							res = s[x+1:]
							print "EXECUTE RES:", res
							val = COMARAPI.COMARValue.load_value_xml(res)
							if val.type == "object":
								retobj = val
							else:
								rx = val
					if rx or len(retobj.data) > 0:						
						if len(retobj.data) > 0:
							if rx:
								print "WARNING: Mixing of Object/Data retvals. Data retvals ignored !"							
							rv = "0 %s" % COMARAPI.COMARValue.dump_value_xml(retobj)
						else:
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

		elif self.mode == "EXEC":
			#hook = OM_MGR.
			pass

	def execCmdHandler(self, From, srcpid, ppid, rfd, pkPid, pkTid, command, pkData):
		print self.procHelper.myPID, "TACALL.execCmdHandler: A exec session cmd captured:", From, srcpid, ppid, rfd, pkPid, pkTid, command #, pkData
		if command == "TRSU_FIN":
			print os.getpid(), self.procHelper.myPID, "A TRSU FIN Captured (ExecSession/ExecCmdHandler):", From, srcpid, ppid, rfd, pkPid, pkTid, command #, pkData
			self.procHelper.sendCommand(int(srcpid), "LNTU_KILL", pkPid, pkTid, pkData)
			self.procHelper.wait_pid(int(srcpid))
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
		elif command == "TRSU_OBJC":
			self.procHelper.sendParentCommand(command, pkPid, pkTid, pkData)
		elif command == "LNTU_KILL":
			self.procHelper.exit()
		elif command == "TRSU_SOBJ":
			print "Register object to TA:", pkData
			self.procHelper.sendParentCommand(command, pkPid, pkTid, pkData)
		elif command == "TRSU_CALL":
			print "InterTA CALL:", pkData
			self.procHelper.sendParentCommand(command, pkPid, pkTid, pkData)

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
			print "XXXXXXXXXXXX Exec Session Child: ", new_ph.myPID, os.getpid(), chldPID, new_ph.myPID, new_ph.gloPPid, cmd, "PRMS:", prms, hook 
			runhook = hook[0](cAPI=ci[0], callerInfo=ci[1], chldHelper = new_ph, OMData = hook[1])
			runhook.loadInstance(hook[2])
			#def runOMNode(self, prms = {}, Type = "", name = "" ):
			cn = name[name.rfind(".")+1:]
			cv = runhook.runOMNode(prms=prms, Type = Type, name = cn)
			print os.getpid(), "Hook returned:", cv.execResult, COMARAPI.COMARValue.CVALget(cv.returnValue)
			rv = "%d %s" % (cv.execResult, COMARAPI.COMARValue.dump_value_xml(cv.returnValue))
			print "XXXXXXXXX Exec Session RetVal:", rv
			new_ph.sendParentCommand("TRSU_FIN", new_ph.myPID, 0, rv)

			while 1:
				print "TACALL:434 Wait for parent LNTU_KILL"
				if new_ph.waitForParentCmd(timeout = 2):
					cmd = new_ph.getParentCommand()
					print "TACALL:437 CMD:",cmd
					if cmd[2] == "LNTU_KILL":						
						break

			new_ph.exit()

api_COMARAPI = None
api_CAPI = None
api_COMARValue = None
