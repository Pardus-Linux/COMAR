#!/usr/bin/python
# -*- coding: utf-8 -*-
# standart python modules
import random
import os
import shutil
import copy
import sys
import types
import gdbm
import timeit
import os.path
import dircache
import cPickle
import md5

# COMAR modules
import comar_global
import COMARValue
from stat import *

OBJ_IAPI 			= None
OBJ_CAPI 			= None
OBJ_OMMGR 			= None
OBJ_HOOKDRV  		= None
CLASS_CINFO 		= None
CLASS_CHLDHELPER	= None
OBJ_COMARValue 		= None


API = None

def checkPerms(perm = "", resource = "", file="", callerInfo = None):
	""" Check access permissions for a object's """
	return 1

class COMARIAPI:
	""" COMAR Core API. This API contain, instance/persistence value
	save/load functions and COMARObject management functions."""
	def	__init__(self, name = ""):
		self.name = name
		self.api_entries = {}
		self.last = 0
		self.modules = {}
		self.cache = {}
		self.hooks = {}
		self.objCacheSize = 32		# Max object cache item count
		self.objCacheTimeout = 180		# Object Cache time out in seconds..
		self.cio_path = comar_global.comar_basic_data # '/var/lib/comard/datadb/'
		self.ns_path = comar_global.comar_instance_data #'/var/lib/comard/nsdata/'
		self.api = API
	def createObjDesc(self, objType = "", instance = "", ci = None):
		obj = objType + ";" + ci.omkey + ";" + instance
		return obj
	def makePDB(self, rawkey):		
		pdb = rawkey.split(":")
		#print "RAWKEY:", rawkey, pdb
		rt = "/"+pdb[0]+"/"+"/".join(pdb[1].split(".")[0:-2])
		return rt
		
	
	def getDBFileKey(self, mode = 'instance', callerInfo = None):
		if callerInfo.mode == "tmp":
			db = callerInfo.pDB
			if db == "":
				db = "temporary"
			dbdir = comar_global.comar_basic_data
			dbroot = dbdir + db + '/'
			dbpath = dbroot + "/" + mode + "/"
		else:
			dbroot = comar_global.comar_instance_data + self.makePDB(callerInfo.OID)
			dbpath = dbroot + "/" + callerInfo.OID.split(".")[-2] + "."
		
		if not os.path.isdir(dbroot):
			try:
				#print "MAKEDIRS:", dbroot
				os.makedirs(dbroot)
			except:
				pass

		#print "Instance dir:", dbpath
		#if not os.path.isdir(dbpath):
		#	os.makedirs(dbpath)
		return dbpath

	def createNewInstance(self, name='', callerInfo = None):
		dbpath_curr = self.getDBFileKey("instance", callerInfo)
		ncallerInfo = copy.deepcopy(callerInfo)
		new = "tmp%08x_%s" % (random.random() * id(callerInfo), name)
		ncallerInfo.OID = new
		dbpath_new = self.getDBFileKey("instance", callerInfo)
		shutil.copytree(dbpath_curr, dbpath_new)
		return ncallerInfo

	def registerObject(self, objid, callerInfo = None):
		""" Register temporary object (not in-memory, its persistent)
		and return a COMARObject.
		followed calls with this object, use this COMARObject."""
		ci = callerInfo
		data = { 'OID'	:ci.OID,
			 'IID'	:ci.IID,
			 'pDB'	:ci.pDB,
			 'mode'	:ci.mode,
			 'node'	:ci.node,
			 'user'	:ci.user,
			 'realm' :ci.realm,
			 'group' :ci.group,
			 'runenv' :ci.runenv,
			 '_objid' :objid }
		#print "HOOKFILE:", ci.hookFile
		ret = COMARValue.COMARObjectDescriptor(objid)
		COMARValue.obj_setData(ret, data)
		return ret

	def destroyObject(self, objid, callerInfo = None):
		return None
	
	def saveValue(self, name = "", value = None, mode = 'instance', callerInfo = None, profile = None):
		""" Save a persistent value to object storage """

		# We can use a hash db, SQL DB etc.
		# But current debug requirements
		# require a simple format.
		if profile:
			pass
			
		dbpath = self.getDBFileKey(mode, callerInfo)
		dbkey = dbpath + name

		dbfile = open(dbkey, 'w')
		dbfile.write(COMARValue.dump_value_xml(value))

		dbfile.close()

	def loadValue(self, name = "", mode = 'instance', callerInfo  = None, profile = None):
		dbpath = self.getDBFileKey(mode, callerInfo)
		dbkey = dbpath + name
		try:
			dbfile = open(dbkey, 'r')
		except:
			return COMARValue.COMARValue("null")

		xml = dbfile.read()
		return COMARValue.load_value_xml(xml)


class COMARCAPI:
	""" Function library API. """
	def __init__(self, api_path=comar_global.comar_modpath + "/capi"):
		self.api_entries = {}
		self.modules = {}
		self.last = 0
		self.modpath = api_path
		self.objHandlers = {}
		self.API = API

	def init(self):
		dl = dircache.listdir
		is_file = os.path.isfile
		files = dl(self.modpath)
		for file in files:
			fname = self.modpath + "/" + file
			if is_file(fname):
				if file[file.rfind("."):] == ".py":
					self.loadModule(fname)
	def reinit(self):
		pass

	def loadModule(self, module = "", modType="python"):
		""" Load a CAPI Module.. """
		if modType == "python":
			new_	= "API" + str(self.last)
			mod = None			#try:
			sys.path.insert(0, os.path.dirname(module))
			file = os.path.basename(module)
			file = file[:file.rfind('.')]
			#print "Try: ", file, "over", sys.path
			try:
				mod = __import__(file)
			except:
				print "Invalid API Module '%s' ignored." % (file)
				sys.path.pop(0)
				return None

			sys.path.pop(0)
			#print "Loaded Module Info:", dir(mod)

			if "API_MODS" in dir(mod):
				new_ = new_ + "_" + mod.APICLASS()
				mod.checkPerms = checkPerms
				for submod in mod.API_MODS:
					modclass = submod(OBJ_IAPI, OBJ_COMARValue)
					vtbl = modclass.GetFuncTable()
					print "Module loading:", module
					vtbl_names = vtbl.keys()
					for i in vtbl_names:
						print "\tAdded Function '%s' from modid: %s" % (i, new_)
						self.api_entries[i] = { "m":new_, "call":vtbl[i] }

					self.modules[new_] = mod
					self.last += 1
					if len(modclass.objHandlers):
						#print "API MGR: Provided Object Handlers over '%s':" % (module)
						for i in modclass.objHandlers:
							self.objHandlers[i] = modclass.objHandlers[i]
							#a = str(self.objHandlers[i][1])
							#a = a.split(" ")
							#print "\t%-33s to %s with %s" % (i, self.objHandlers[i][0] a[2])
			#except:
			#	if mod != None:
			#		del mod
			#	return None
	def has_function(self, name):
		return self.api_entries.has_key(name)

	def call(self, method = "", prms = {}, callerInfo = None):
		""" Primary API call entry for installable API funcs """
		if self.api_entries.has_key(method):
			ret = self.api_entries[method]["call"](method, prms, checkPerms, callerInfo)
			return ret
		else:
			return None



class OM_MANAGER:
	def __init__(self):
		self.dbhelper = None
		self.ompath  = comar_global.comar_modpath + "/om_drivers"
		self.omdrvs = {}
		# OM DRVS Call Format..
		# callInfo = OBJ_CALLINFO, objAPI = DEFAULT_CAPI, useNS = "ns.."
		# callInfo = None, objAPI = None, useNS = ""
		self.OMS	= {}
		self.objHandlers = {}

		#print "OBJ_API:", OBJ_API, dir(OBJ_API)
		print "Loading OM Handlers..", self.ompath

		dl = dircache.listdir
		is_file = os.path.isfile

		files = dl(self.ompath)
		for file in files:
			fname = self.ompath + "/" + file
			if is_file(fname):
				if file[file.rfind("."):] == ".py":
					self.loadOMHandler(fname)

		print "Provided OM Drivers:", self.omdrvs.keys()
		capiHandlers = API.CAPI.objHandlers
		for i in capiHandlers.keys():
			self.objHandlers[i] = capiHandlers[i]
			
	def getCInfo(self, node, nodeKey, user, conn, caller):
		n = self.parseNodeName(node)
		if not n:
			print "OMMGR: Invalid OM Node", node
			return 1
		NS = n[0]
		node = n[1]
		nid = nodeKey[nodeKey.find(":")+1:]
		n = self.OMS[NS].getCINFO(nid)
		ci = n[1]
		# PDB. This is a pathname (relative to $comar_global.comar_data/datadb) for save persistent values.
		# This value typically selected from profile information
		ci.pDB = "" # Set form profile db.
		ci.callStack = None	#
		ci.node = NS+":"+node
		# User for this call
		ci.user = user.name
		ci.realm = user.realm
		ci.group = user.group
		ci.caller = caller
		# Run environment. CSL -> CSL Interpreter. PYTHON -> PY interpreter..
		return (n[0], ci)

	def parseNodeName(self, node):
		n = node.split(":")
		if len(n) != 2:
			return None
		return (n[0], n[1])

	def addObjHandlers(self, obj):
		if hasattr(obj, "objHandlers"):
			if len(obj.objHandlers):
				print "OM MGR: Registering Object Handlers from '%s':" % (obj.__class__)
				for i in obj.objHandlers:
					self.objHandlers[i] = obj.objHandlers[i]
					a = str(self.objHandlers[i])
					a = a.split(" ")
					print "\t%-33s to %s with %s" % (i, self.objHandlers[i][0], a[3])

	def	initOM(self, nameSpace, Type, omDefFile):
		global OBJ_API, API
		#self.omdrvs[nameSpace]
		if self.OMS.has_key(nameSpace):
			print "NameSpace '%s' already initalized.." % (nameSpace)
			return None

		if not self.omdrvs.has_key(Type):
			print "OM Handler '%s' for NameSpace '%s' not found.." % (Type, nameSpace)
			return None

		drv = self.omdrvs[Type]
		om = drv(callInfo = API.proto_callerInfo, objAPI = API, useNS = nameSpace, defFile=omDefFile, mainOMGR = self)
		om.setDBHelper(self.dbhelper)
		om.postInit()
		self.OMS[nameSpace] = om
		self.addObjHandlers(om)
		#lngs = om.Interpreters
		#for i in lngs:
		#	if self.ipts.has_key(i):
		#		print "\nWarning !!! OM Driver '%s' override language interpreter '%s'\n" % (Type, i)
		#	self.ipts[i] = om

		#print "OM: '%s' with driver '%s' initialized succesfully" % (nameSpace, Type)
		#if len(lngs):
		#	print "\tOM Driver '%s' provide interpreter for '%s' language(s)" % (Type, lngs)

	def OMHandler(self, nameSpace):
		if self.OMS.has_key(nameSpace):
			return self.OMS[nameSpace]

	def loadOMHandler(self, module):
		mod = None			#try:
		sys.path.insert(0, os.path.dirname(module))
		file = os.path.basename(module)
		file = file[:file.rfind('.')]
		#print "Try: ", file, "over", sys.path
		mod = __import__(file)
		try:
			mod = __import__(file)
		except:
			print "Invalid OM Handler Module '%s' ignored" % (file)
			sys.path.pop(0)
			return None

		sys.path.pop(0)
		#print "Loaded Module Info:", dir(mod)
		if "OM_BINDINGS" in dir(mod):
			#print "\tOM handler for OM Type:", mod.OM_BINDINGS.keys(), "from", module
			for bind in mod.OM_BINDINGS.keys():
				self.omdrvs[bind] = mod.OM_BINDINGS[bind]
		else:
			#print "'%s' is not a OM Handler Module (can be a library?). Ignored" % (file)
			del mod
			return None

	def setDBHelper(self, helper):	
		self.dbhelper = helper
		#print "NAMESPACE API Initialized with", helper, self.OMS.values()
		for i in self.OMS.values():					
			print i.setDBHelper
			i.setDBHelper(self.dbhelper)

	def addOMCode(self, node = "", IID = "", code = "", fileName="", scriptType="CSL"):
		n = self.parseNodeName(node)
		if not n:
			print "OMMGR: Invalid OM Node", node
			return 1
		NS = n[0]
		node = n[1]
		if hasattr(self.OMS[NS], "addOMCode"):
			return self.OMS[NS].addOMCode(node, IID, code, fileName, scriptType)
	#addOMPrePostScript
	# addOMPrePostScript(NS, node, IID, code, entry, Loc, scriptType)
	# addOMPrePostScript(NS, node, OMObject, entry, Loc)
	# addOMPrePostScript(NS, node, EventID, Loc)
	def addOMPrePostScript(self, node="",IID="",code="",fileName="",OMObject="",entry="",EventID="",Loc="PRE",scriptType="CSL"):
		n = self.parseNodeName(node)
		if not n:
			print "OMMGR: Invalid OM Node", node
			return 1
		NS = n[0]
		node = n[1]
		if hasattr(self.OMS[NS], "addOMPrePostScript"):
			return self.OMS[NS].addOMPrePostScript(node,IID,code,fileName,OMObject,entry,EventID,Loc,scriptType)

	def getOMObjList(self, node = ""):
		n = self.parseNodeName(node)
		print n
		if not n:
			print "OMMGR: Invalid OM Node", node
			return []
		NS = n[0]
		node = n[1]

		if self.OMS.has_key(NS) and hasattr(self.OMS[NS], "getOMObjList"):
			rt = self.OMS[NS].getOMObjList(node)
			ret = []
			for i in rt:
				ret.append("%s:%s" % (NS, i))
			return ret
		return []

	def getOMObj(self, key = ""):
		n = []
		if key.find(":") == -1:
			print "OMMGR: Invalid OM Key", key
			return None
		n.append(key[:key.find(":")])
		n.append(key[key.find(":")+1:])
		NS = n[0]
		node = n[1]
		print "NS/node:", NS, node
		if self.OMS.has_key(NS):
			if hasattr(self.OMS[NS], "getOMObj"):
				return self.OMS[NS].getOMObj(node)

	def getOMProperties(self, key):
		n = []
		if key.find(":") == -1:
			print "OMMGR: Invalid OM Key", key
			return None
		n.append(key[:key.find(":")])
		n.append(key[key.find(":")+1:])
		NS = n[0]
		node = n[1]
		print "OM_MGR: NS/node:", NS, node
		if self.OMS.has_key(NS):
			return self.OMS[NS].getOMProperties(node)

	def getObjHook(self, langid = ""):
		global COMARAPI
		return OBJ_HOOKDRV.getInterpreter(langid)

	def checkAccess(self, callerInfo = None, node = ""):
		n = self.parseNodeName(node)

		if not n:
			return None
		NS = n[0]
		node = n[1]
		if self.OMS.has_key(NS) and hasattr(self.OMS[NS], "checkAccess"):
			return self.OMS[NS].checkAccess(node)
		return 1 # OM Not uses acl checking..


class OBJ_HOOK_DRV:
	def __init__(self):
		self.objhooks = {}
		self.objHandlers = {}
		modpath = comar_global.comar_modpath + "/langdrv"
		dl = dircache.listdir
		is_file = os.path.isfile
		print "Loading OM Script Handlers.."
		files = dl(modpath)
		for file in files:
			fname = modpath + "/" + file
			if is_file(fname):
				if file[-3:] == ".py":
					self.loadObjHook(fname)

	def	providedIpts(self):
		return self.objhooks.keys()

	Interpreters = property(providedIpts, None, None)

	def loadObjHook(self, module):
		mod = None			#try:
		sys.path.insert(0, os.path.dirname(module))
		file = os.path.basename(module)
		file = file[:file.rfind('.')]
		#print "Try: ", file, "over", sys.path
		try:
			mod = __import__(file)
		except:
			#print "Invalid ObjHook Module '%s' ignored" % (file)
			sys.path.pop(0)
			return None

		sys.path.pop(0)
		#print "Loaded Module Info:", dir(mod)
		if "_HOOK" in dir(mod):
			print "\tObject hook for script type:", mod._INTERPRETER, "from", module
			lang = "" + mod._INTERPRETER[:] + ""
			hook = mod._HOOK
			self.objhooks[lang] = hook
			h = hook(cAPI = None)
			for i in h.objHandlers:
				a = str(h.objHandlers[i])
				a = a.split(" ")
				self.objHandlers[i] = (lang + ":" + a[2].split(".")[1], self.cObjHandler)
				#print "\t%-33s to %s" % (i, self.objHandlers[i])
		else:
			#print "'%s' is not a ObjHook Module (can be a library?). Ignored" % (file)
			return None
	def getInterpreter(self, langid = "CSL"):
		if langid in self.objhooks.keys():
			return self.objhooks[langid]

	def cObjHandler(self, objClass = "", objid = "", callType = "", callName = "", prms = {}, callerInfo = None):
		pass


class COMARAPI:
	def __init__(self):
		#print "Module Dir:",dir(), DEFAULT_CAPI
		self.IAPI 				= OBJ_IAPI				# COMAR Core Functions. saveValue etc.
		self.CAPI 				= OBJ_CAPI				# Library functions for CSL.
		self.checkPerms			= checkPerms			# checkPerms for function calls.
		self.makeinstance 		= None
		self.api_OBJHOOK 		= OBJ_HOOKDRV
		self.COMARValue			= OBJ_COMARValue
		self.proto_callerInfo	= CLASS_CINFO				# callerInfoObject.
		self.proto_childHelper	= CLASS_CHLDHELPER

class callerInfoObject:
	def __init__(self):
		# Object ID. Uses for createNewInstance and OM Calls.
		# if mode == tmp, this is a temporary object, elsewhere
		#    this is a indicate OM Node call name.
		self.OID = ""
		# Package Interface ID
		# This is set for exec session with use PackageManager API.
		# Indicate application IID for requested script.
		# if this is a "UI", indicate TA EXEC call..
		self.IID = ""
		# PDB. This is a pathname (relative to $comar_global.comar_data/datadb) for save persistent values.
		# This value typically selected from profile information
		self.pDB = ""
		# Object mode. "tmp" -> Temporary object. "om" -> OM Object..
		self.mode = "tmp"		#
		# CallStack. This is a reserved for future use.
		self.callStack = None	#
		# Original node. If this is a object, this property contain real object's name.
		self.node = ""
		# User for this call
		self.user = "comar"
		self.realm = "localhost"
		self.group = "comar"
		self.caller = ""
		self.omkey  = ""
		# Run environment. CSL -> CSL Interpreter. PYTHON -> PY interpreter..
		self.runenv = "CSL"
		self.TAData = None
