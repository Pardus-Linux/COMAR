# EXEC.PY
#
# EXEC SESSION PROVIDER.

import os, sys, select

class	execSessProvider:
	def	__init__(self, sessMgr = None, conn = None, user = None, caller = None):
		self.mode		= ""
		self.user		= user
		self.conn		= conn
		self.callEntry	= ""
		self.callType	= ""
		self.prms		= {}
		self.callCode	= None
		self.obj		= None
		self.procHelper	= sessMgr
		self.TIDS		= 0
		self.status		= "UNKNOWN"
		self.TTSID		= ""
	def	setCode(self, code, name):
		self.callCode 	= code
		self.mode 		= "EXEC"
	def	setObject(self, obj, name):
		self.obj 		= obj
		self.callEntry	= name
		self.mode		= "OBJCALL"
	def setOMCall(self, omnode, callType):
		self.callEntry	= omnode
		self.callType	= callType
		self.mode		= "OMCALL"
	def	setPrms(self, prms = {}):
		for i in prms.keys():
			self.prms[i] = prms[i]
	def	run(self):
		if self.mode == "OMCALL":
			callEntry = self.callEntry
			callType  = self.callType
			if self.checkOMACLSet(callEntry, callType):
				self.procHelper.sendParentCmd("SNSU_DENY", self.procHelper.myPID, self.TIDS, None)
				return 1
			if self.checkUserACL():
				self.procHelper.sendParentCmd("SNSU_DENY", self.procHelper.myPID, self.TIDS, None)
				return 1

		# Check PRE Scripts..
		print "We run with:", self.mode, self.callEntry, self.prms,
		self.TIDS += 1
		self.procHelper.sendParentCommand("SNSU_QUE", self.procHelper.myPID, self.TIDS, None)
		self.procHelper.cmdHandler = self.cmdProcessor
		self.procHelper.addSessionCommand([	"TNTU_KILL", "SNSU_PRC", "MNTB_TERM", "TRTU_RES",
											"TRTU_SSID", "MNTU_SLP", "MNTU_AWQ" , "TRTU_LRUN",
											"TRTU_COM",  "TNTU_RDY", "TNTU_ERR" , "SNSU_FTL",
											"TNSU_GET" ])
		print "Wait for childs.."
		ret = self.procHelper.ProcessIO()
		print "Returned FDSET:", ret
		select.select([],[],[],0.8)
		return
	def	register(self, rpc = None):
		if rpc.Type == "OMCALL":
			self.prms = rpc.getPropertyMulti("parameter", all=1)
			self.setOMCall(rpc["name"], rpc["type"])
		elif rpc.Type == "OBJCALL":
			self.prms = rpc.getPropertyMulti("parameter", all=1)
			self.setObject(rpc["object"], rpc["name"])
		elif rpc.Type == "EXEC":
			self.prms = rpc.getPropertyMulti("parameter", all=1)
			self.setCode(rpc["object"], rpc["name"])
		else:
			return 1
		self.TTSID  = rpc.TTSID
		self.status = "QUEUED"
		return 0
	def	checkOMACLSet(self, callEntry, callType):
		return 0
	def	checkUserACL(self):
		return 0
	def	cmdProcessor(self, From, srcpid, ppid, rfd, pkPid, pkTid, command, pkData):
		pass

class callerInfoObject:
	def	__init__(self):
		self.TTSID		= ""
		self.IID		= ""
		self.pDB		= ""
		self.mode		= "tmp"
		self.callStack	= []
