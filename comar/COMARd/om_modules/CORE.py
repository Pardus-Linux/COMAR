#!/usr/bin/python
# -*- coding: utf-8 -*-
import dircache, os, sys, copy
import comar_global

class OM_CORE:
	def __init__(self, callInfo = None, objAPI = None, useNS = "", defFile = "", mainOMGR = None):
		global CV
		self.dbhelper = None
		self.callInfo = callInfo
		self.objAPI = objAPI
		self.useNS  = useNS
		self.main	= mainOMGR
		self.cv		= objAPI.COMARValue
		path = os.path.dirname(__file__)
		sys.path.insert(0, path)
		self.event	= __import__('CORE_EVENT')
		self.ommgmt	= __import__('CORE_OMMGMT')
		self.nodes = {}
		self.nodeProcessor = None
		self.eventProcessor = None
		self.objHandlers = {}
		#print "OM_CORE Installed:"
		#for i in dir(objAPI):
		#	print "OM_CORE:", i, "=", getattr(objAPI, i)
			
	def getCINFO(self, nodeKey):
		ci = self.callInfo()		
		ci.IID = "EMBED_CORE"
		ci.OID = "CORE:" + ci.IID + "." + nodeKey
		ci.mode = "auto"
		return (self.objAPI, ci)

	def setDBHelper(self, helper):
		self.dbhelper = helper
		print "CORE-COMPOUND:", self.cv
		self.nodeProcessor	= self.ommgmt.objModelMgr(dbHelper = helper, CV = self.cv, OMMGR=self.main)
		self.eventProcessor = self.event.eventSubsystem(dbHelper = helper, CV = self.cv, OMMGR=self.main)

	def postInit(self):
		# postInit called after setting dbhelper		
		mvtbl = self.nodeProcessor.methodVtbl
		for i in mvtbl.keys():
			self.nodes[i] = mvtbl[i]
		mvtbl = self.nodeProcessor.propVtbl
		for i in mvtbl.keys():
			self.nodes[i] = mvtbl[i]
		mvtbl = self.eventProcessor.methodVtbl
		for i in mvtbl.keys():
			self.nodes[i] = mvtbl[i]
		mvtbl = self.eventProcessor.propVtbl
		for i in mvtbl.keys():
			self.nodes[i] = mvtbl[i]
		mvtbl = self.nodeProcessor.objDriver
		for i in mvtbl.keys():
			self.objHandlers[i] = mvtbl[i]
		mvtbl = self.eventProcessor.objDriver
		for i in mvtbl.keys():
			self.objHandlers[i] = mvtbl[i]
		print "CORE DB Initialization success"
		if 0:
			print "CORE OM NODE MAP:"
			ke = self.nodes.keys()
			ke.sort()
			for i in ke:
				a = str(self.nodes[i])
				a = a.split(" ")
				print "\t%-33s to %s" % (i,a[2])
			ke = self.objHandlers.keys()
			ke.sort()
			print "CORE OM STD OBJECT HANDLERS MAP:"
			for i in ke:
				a = str(self.objHandlers[i])
				a = a.split(" ")
				print "\t%-33s to %s" % (i,a[2])

	def getOMObjList(self, node = ""):
		# Require a bit work.
		# USE dbHalper API !!!
		if self.nodes.has_key(node):
			return [node]
		return []

	def getOMObj(self, key = ""):
		if self.nodes.has_key(key):
			return (genericObjHook, self, key)
		else:
			return None
	def getOMProperties(self, key = ""):
		if self.nodes.has_key(key):
			return [0]
		else:
			return None


class genericObjHook:
	useContainer = False
	canPersist   = False
	def __init__(self, cAPI = None, callerInfo = None, chldHelper = None, OMData = None):
		self.OMProvider = OMData
		self.OMEntry = None
		self.cAPI = cAPI		
		self.callerInfo = callerInfo
		self.procHelper = chldHelper
	def loadInstance(self, instanceid = ""):
		if self.OMProvider.nodes.has_key(instanceid):
			self.OMEntry = self.OMProvider.nodes[instanceid]
			print "OM ENTRY SET:", instanceid
		return None
	def setSourceFromDBKey(self,dbfile = "",  key = ''):
		return None
	def setSourceFromURL(self, src = ''):
		return None
	def setSourceFromBuffer(self, buffer = ''):
		return None
	def compile(self, buffer):
		return None
	def runOMNode(self, prms = {}, Type = "", name = "" ):
		print "HOOK Run:", self.OMEntry, prms
		if self.OMEntry:
			ret = self.OMEntry(prms = prms, callerInfo = self.callerInfo)
			if not ("execResult" in dir(ret)):
				return self.cAPI.COMARValue.COMARRetVal(0, ret)
			else:
				return ret


OM_BINDINGS = { "CORE":OM_CORE }
