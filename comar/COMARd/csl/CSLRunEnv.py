# standart python modules
import copy
import types
import sys
import os
import cPickle
import urlparse, gzip
import dircache

import comar_global
comar_dir = comar_global.comar_modpath
csl_dir = os.path.join(comar_dir, "csl_mods")
sys.path.append(csl_dir)

import RPCData
# CSL modules
import CSLParser


_INTERPRETER = 'CSL'

DEBUG_FATAL = 0
DEBUG_PARSER = 1
DEBUG_ARROP = 2
DEBUG_TREE = 4
DEBUG_LET =  8
DEBUG_USR = 16
DEBUG_PRST = 32
DEBUG_EXP = 64
DEBUG_CALL = 128

def haskey(dict, nkey):
	if dict == None:
		return 0
	key = arrkeyfix(nkey)
	if dict.has_key(key):
		return 1
	else:
		try:
			if type(key) == type(""):
				r = dict.has_key(int(key))
			else:
				r = dict.has_key(str(key))
		except:
			r = 0
		return r

def arrkeyfix(keyn):
	key = copy.deepcopy(keyn)
	if type(key) == type(""):
		try:
			r = float(key)
			return arrkeyfix(r)
		except:
			return key
	elif type(key) == type(1) or type(key) == type(1.0):
		if float(key) == int(key):
			return int(key)
	else:
		return key

class	CSLCapsule:
	""" CSLCapsule: An object for Execution Environment of CSL Language. """
	# Features List:
	# Persistency values determine		: SUCCESS
	# Persistency values save			: SUCCESS
	# Persistency values restore		: SUCCESS
	# MakeInstance 						: SUCCESS
	# Array Values						: Success, not well tested..
	# Profile Management				: Parsed only..
	# COMAR->CSL Numeric				: SUCCESS
	# COMAR->CSL String					: SUCCESS
	# COMAR->CSL Array					: SUCCESS
	# COMAR->CSL Object					: SUCCESS
	# CSL->COMAR Numeric				: SUCCESS
	# CSL->COMAR String					: SUCCESS
	# CSL->COMAR Array					: SUCCESS
	# CSL->COMAR Object					: SUCCESS
	# InterObject Property call			: SUCCESS
	# InterObject Method call			: SUCCESS
	# InterObject Function call			: SUCCESS
	# COMARtoCSL Property call			: SUCCESS
	# COMARtoCSL Method call			: SUCCESS
	# COMARtoCSL Function call			: SUCCESS
	# External Property call			: Defined only
	# External Method call				: Defined only
	# External Function call			: Defined only
	# CAPI Call							: CSL-CAPI Success, COMAR-CAPI work continue..
	# Object Interface Entries			: SUCCESS
	# LoadObject						: SUCCESS
	# treeCoder, preprocessor			: Partially Success:
	#	TreeCoder 'cmds'				: SUCCESS
	#	treeCoder 'alias'				: SUCCESS
	#	treeCoder make vtbl				: SUCCESS
	#	treeCoder persistent			: SUCCESS
	# Object Type Handling				: SUCCESS, but not well tested..
	# External Object Handling			:
	#	CSLCheckValue object dedect		: SUCCESS
	#	CSLInterpreter object "LET"		: SUCCESS
	#   Others ????						: ???
	# Save Machine State				: N/A
	# makeinstance implementation		: SUCCESS
	# destroy implementation			: N/A
	# register implementation			: Parsed only
	# "me" implementation				: SUCCESS
	# Garbage Collection				: N/A
	# obj.function() type func call		: SUCCESS, but not well tested..
	# select/case implementation		: N/A
	# delete implementation				: SUCCESS, but not well tested..

	def	__init__(self, instance = "", nsAPI = None, extObjEntry = None, callerInfo = None):
		self.Obj = None				# Code block.
		self.Tbl = {}				# Code tbls.

		self.root = None

		self.decl 			= [ "deffunc", "defmethod", "defprop" ] # internal, used by treeCoder, etc.
		self.vtbl			= {}		# vtbl, interface entry points.
		self.current_cb 	= None		#
		self.instance 		= instance	# instance id.
		self.ipts 			= {}		# CSL cmd interpreters, inused
		self.nsAPI 			= nsAPI	    # NameSpaces, call entry points..
		self.COMARAPI		= nsAPI.IAPI
		self.CAPI			= nsAPI.CAPI
		self.COMARValue		= nsAPI.COMARValue
		self.ExtObjCall		= extObjEntry
		self.callerInfo 	= callerInfo
		self.lastLTbl 		= None
		self.lTblStack 		= []
		self.codeStack 		= []
		self.sessionStack 	= []
		self.sessionID 		= 0
		self.tc 			= 0
		self.procStack 		= []
		self.dbgf = None #open("csldebug", "w")
		self.debugfile = None
		self.debuglvl = 0 #DEBUG_CALL
		self.modpath = csl_dir 
		self.cslAPIS = {}
		self.cslAPIMods = []
		self.loadCSLApimods()
		
		
	def loadCSLApimods(self):
		dl = dircache.listdir
		is_file = os.path.isfile
		files = dl(self.modpath)
		for file in files:
			fname = self.modpath + "/" + file
			#print "CSL MOD Check FName:", file
			if is_file(fname):
				if file[file.rfind("."):] == ".py":
					self.loadModule(fname)
					
	def loadModule(self, module = "", modType="python"):
		""" Load a CAPI Module.. """
		if modType == "python":			
			mod = None			#try:
			sys.path.insert(0, os.path.dirname(module))
			file = os.path.basename(module)
			file = file[:file.rfind('.')]
			#print "Try: ", file, "over", sys.path
			try:
				mod = __import__(file)
			except:
				print "Invalid CSL API Module '%s' ignored." % (file)
				sys.path.pop(0)
				return None
			sys.path.pop(0)
			#print "Loaded Module Info:", dir(mod)
			if "CSLAPI_NAME" in dir(mod):				
				mod.CSLValue = CSLValue
				mod.debug = self.debug
				vtbl = mod.getFuncTable()
				#print "CSL Module loader:", module
				vtbl_names = vtbl.keys()
				for i in vtbl_names:
					#print "\tAdded Function '%s' from module: %s (%s)" % (i, mod.__file__, vtbl[i].__class__)
					self.cslAPIS[i] = vtbl[i]
				self.cslAPIMods.append(mod)
				
	def debug(self, level=0, *msg):
		if (level == DEBUG_FATAL) or (level & self.debuglvl) > 0:
			if self.debugfile:
				f = open("cslre-%s.log" % api_os.getpid(), "a")
				m = "%s %s %s " % (self.callerInfo.node, "--", os.getpid())
				print self.name, self.mode, os.getpid(),
				for i in msg:
					m = m + " " + str(i)
					print i,
				print
				f.write(m+"\n")
				f.close()
			else:
				print "CSLRE:", os.getpid(),
				for i in msg:
					print i,
				print

#--------------------------------------------------------------
# Tokenization, Parsing, code loading.
#--------------------------------------------------------------
	def	compileResult(self):
		return cPickle.dumps({"tree":self.root, "tbl":self.Tbl, "vtbl":self.vtbl})

	def	loadPreCompiled(self, pdata):
		pd = cPickle.loads(pdata)
		self.root = pd["tree"]
		self.Tbl  = pd["tbl"]
		self.vtbl = pd["vtbl"]		
		#self.printTree()

	def	LoadObject(self, fileName = ""):
		CPO = CSLParser.CSLParse(file = fileName)

		if CPO == None:
			return None

		tree = CPO.tree
		self.Obj = CPO
		self.Tbl = { "A":CPO.ATbl, "I":CPO.ITbl, "F":CPO.FTbl,
					"Q":CPO.QTbl, "N":CPO.NTbl, "O":CPO.OTbl }

		self.root = copy.deepcopy(tree)

		self.decl = [ "deffunc", "defmethod", "defprop" ]
		self.current_cb = None

		if tree.type == "ROOT" and tree.data != "binded":
			self.CSLTreeCoder(self.root)

		#self.printTree()
		#print self.vtbl
	def printTree(self):
		print "SYMBOL TABLE:"
		n = self.Tbl.keys()
		n.sort()
		for main in n:
			t = self.Tbl[main].keys()
			t.sort()
			if main in "AFO":
				for idf in t:
					print main, idf, self.Tbl[main][idf]
			else:
				print main,
				for idf in t:
					print idf, "=", self.Tbl[main][idf], ",",
				print

		self.printTreeNode(self.root)

	nest = 0
	def printTreeNode(self, a):
		x = 0
		this = self
		while a != None and x < 18:
			for i in range(0, this.nest): print "    ",
			print a.type, "->", a.data,
			if a.child != None:
				print "GO CHILD"
				this.nest += 1
				this.printTreeNode(a.child)
				this.nest -= 1
				a = a.next
			elif a.next != None:
				print "GO NEXT"
				a = a.next
			else:
				print "END.."
				a=None
			x += 1

	def	LoadBuffer(self, codeBuffer = ""):
		if codeBuffer == "":
			return None
		CPO = CSLParser.CSLParse(code = codeBuffer)

		if CPO == None:
			return None

		tree = CPO.tree
		self.Obj = CPO
		self.Tbl = { "A":CPO.ATbl, "I":CPO.ITbl, "F":CPO.FTbl,
					"Q":CPO.QTbl, "N":CPO.NTbl, "O":CPO.OTbl }

		self.root = copy.deepcopy(tree)

		self.decl = [ "deffunc", "defmethod", "defprop" ]
		self.current_cb = None

		if tree.type == "ROOT" and tree.data != "binded":
			self.CSLTreeCoder(tree)

	def CSLTreeCoder(self, tree = None):

		while tree != None:
			tree.codeLine = self.tc

			#print self.tc, "->", tree.type, tree.data
			self.tc += 1
			if self.ipts.has_key(tree.type):
				# basic commands (if, for etc..)
				if self.ipts.has_key(tree.type):
					tree.data["entry"] = self.ipts[tree.type]
				self.CSLTreeCoder(tree.child)
				tree = tree.next

			elif tree.type == "ROOT":
				# go child immediately..
				tree.data = "binded"
				tree = tree.child

			elif tree.type in self.decl:
				#print "DECL: '%s' in " % ( tree.type ), tree.data
				self.current_cb = tree.data
				if tree.type == "defprop":
					# special case. We are create name_get and
					# name_set node.
					tmp = copy.copy(tree)
					tree = tree.child
					tmp.data["alias"] = {}
					tmp.data["persistent"] = []
					tmp.data["instance"] = []

					while tree != None:
						if tree.type == "get":
							tmp.data[tmp.data["name"] + "_get"] = tree
							self.vtbl["p_" + tmp.data["name"] + "_get"] = tree

							self.CSLTreeCoder(tree.child)
						elif tree.type == "set":
							tmp.data[tmp.data["name"] + "_set"] = tree
							self.vtbl["p_"+tmp.data["name"] + "_set"] = tree

							self.CSLTreeCoder(tree.child)
						else:
							return None
						tree = tree.next
					tree = tmp.next
				else:

					self.vtbl[tree.type[3]+"_"+tree.data["name"]] = tree
					self.CSLTreeCoder(tree.child)
					tree = tree.next

			elif tree.type == "alias":

				if self.current_cb.has_key("alias"): # Already defined?
					tmp = self.current_cb["alias"]
					# seek old identifier and add new aliases..
				else:
					tmp = {}
					self.current_cb["alias"] = tmp

				arr = tree.data['aliases']
				for i in arr:
					tmp[i] = tree.data['identifier']



				tree = tree.next
			elif tree.type == "persistent":
				# Get previously saved values..
				if self.current_cb.has_key("persistent"): # Already defined?
					tmp = self.current_cb["persistent"]
					# seek old identifier and add new aliases..

				else:
					tmp = []
					self.current_cb["persistent"] = tmp

				for i in tree.data['variables']:
					tmp.append(i)

				tree = tree.next

			elif tree.type == "instance":
				# Get previously saved values..
				if self.current_cb.has_key("instance"): # Already defined?
					tmp = self.current_cb["instance"]
					# seek old identifier and add new aliases..
				else:
					tmp = []
					self.current_cb["instance"] = tmp
				for i in tree.data['variables']:
					tmp.append(i)

				tree = tree.next
			else:

				tree = tree.next


	def GetInterfaceInfo(self):
		"Return interface info (methods, prms, props.. etc. ) for Capsule."
		ret = []
		tree = self.root.child

		while tree != None:
			if tree.type == "defmethod":
				prm = []
				for i in tree.data["prmlist"].keys():
					prm.append(i);

				ret.append({ "method":tree.data["name"],  "prmlist":prm  })

			elif tree.type == "defprop":
				ret.append({ "property":tree.data["name"], 'prmlist':[ tree.data["prm"] ] })

			elif tree.type == "deffunc":
				prm = []
				for i in tree.data["prmlist"].keys():
					prm.append(i);

				ret.append({ "function":tree.data["name"], 'prmlist' :prm })

			else:
				tree = tree.next

		return ret

#---------------------------------------------------------------------
# Code and Variable persistency procedures..
#---------------------------------------------------------------------
	def	SaveTree(self, buf = ''):
		pass

	def saveMachineState(self, codeEntry = None, localTbl = {}, codeStack = [], dataStack = []):
		# Save current parsed code.. (Not needed)
		# Save Global Expression Table Tbl
		# Save Current Expression..
		pass

	def loadMachineState(self):
		# Load Machine Stack, data stack etc..
		# Call CSL Interpreter with this stacks and localTbl
		pass

	def CSLPersistSet(self, name, val, index = ""):

		key = self.procStack[-1] + '_p.' + name + '.' + index
		value = self.CSLtoCOMARValue(val)
		self.COMARAPI.saveValue(key, value, 'persist', self.callerInfo)

	def	CSLPersistGet(self, name, index = ""):
		key = self.procStack[-1] + '_p.' + name + '.' + index
		value = self.COMARAPI.loadValue(key, 'persist', self.callerInfo)
		return self.COMARtoCSLValue(value)

	def CSLPersistDestroyVal(self, name,val, index = ""):
		self.debug(DEBUG_PRST, "PERSIST DESTROY PASSED: ", name, val, index)

	def CSLInstanceSet(self, name, val, index = ""):
		key = name + '.' + index
		value = self.CSLtoCOMARValue(val)
		self.COMARAPI.saveValue(key, value, 'instance', self.callerInfo)
		#print "INSTANCE SET PASSED: ", name, val, index

	def	CSLInstanceGet(self, name, index = ""):
		key = name + '.' + index
		value = self.COMARAPI.loadValue(key, 'instance', self.callerInfo)
		return self.COMARtoCSLValue(value)

	def CSLInstanceDestroyVal(self, name,val, index = ""):
		self.debug(DEBUG_PRST, "INSTANCE DESTROY PASSED: ", name, val, index)

#------------------------------------------------------------------------
# COMAR <-> CSL value conversation..
#------------------------------------------------------------------------
	def COMARtoCSLValue(self, comarVal, root = None, oldkey = ""):
		if hasattr(comarVal, "execResult"):
			if comarVal.execResult != 0:
				return CSLValue(typeid = "NULL", value = None)				
			comarVal = comarVal.returnValue
			
		if comarVal == None:
			return CSLValue(typeid = "NULL", value = None)
		if comarVal.type == "string":
			return CSLValue(typeid = "string", value = comarVal.data.value)
		elif comarVal.type == "numeric":
			return CSLValue(typeid = "numeric", value = comarVal.data)
		elif comarVal.type == "array":
			comarArrItem = copy.copy(comarVal.data)
			if root == None:
				ret = CSLValue(typeid='array', value = {})
			else:
				ret = root
			while comarArrItem:
				key = comarArrItem.Key[:]
				#if oldkey != '':
				#	nkey = oldkey + "\\" + key
				#else:
				#	nkey = key				
				key = arrkeyfix(key)
				val = self.COMARtoCSLValue(comarArrItem.item, root)
				if val != None:
					ret.value[key] = val

				comarArrItem = comarArrItem.next
			if root == None:
				return ret
			else:
				return None
		elif comarVal.type == "object":
			return CSLValue(typeid = "object", value = comarVal.data)

		return None

	def CSLtoCOMARType(self, cslVal):
		if cslVal.type == "string":
			return "string"

		elif cslVal.type == "numeric" or cslVal.type == "boolean":
			return "numeric"

		elif cslVal.type == "array":
			return "array"

	def CSLtoCOMARValue(self, cslVal):
		if cslVal.type == "string":
			return self.COMARValue.string_create(cslVal.toString())

		elif cslVal.type == "numeric" or cslVal.type == "boolean":
			return self.COMARValue.numeric_create(cslVal.value)

		elif cslVal.type == "array":
			arr = self.COMARValue.array_create()
			for key in cslVal.value.keys():				
				self.COMARValue.array_additem(arr, key, 0, self.CSLtoCOMARValue(cslVal.value[key]))
			return arr
			
		elif cslVal.type == "object":
			#print "To COMAR Object:", cslVal.value, self.COMARValue.COMARValue("object", cslVal.value)
			return self.COMARValue.COMARValue("object", cslVal.value)

		return self.COMARValue.null_create()

	def	CSLBuildPrmList(self, COMARPrms = {}):
		if COMARPrms == None:
			return {}

		prmNames = COMARPrms.keys()
		ptbl = {}
		for key in prmNames:
			ptbl[key] = self.COMARtoCSLValue(COMARPrms[key])

		return ptbl
#-----------------------------------------------------------------------------
# Entry points for outside world. This API called from COMAR.
#-----------------------------------------------------------------------------
	def	runPropertyGet(self, name = "__default", prms = {}):
		""" Called from COMAR Container/objhook. prms is COMARValue  """
		prmtbl = self.CSLBuildPrmList(prms)
		index = None
		if prmtbl.has_key("index"):
			index = prmtbl["index"]
		res = self.callPropertyGet(name, index)
		self.debug(DEBUG_CALL, "CSL PGET:", res, res.type, res.value)
		if res.type == "NULL":
			return self.COMARValue.COMARRetVal(1, None)
		else:
			return self.COMARValue.COMARRetVal(0, self.CSLtoCOMARValue(res))

	def	runPropertySet(self, name = "__default", prms = {}):
		""" Called from COMAR Container/objhook. prms + value is COMARValue  """
		prmtbl = self.CSLBuildPrmList(prms)
		index = None
		value = None
		if prmtbl.has_key("index"):
			index = prmtbl["index"]
		if prmtbl.has_key("value"):
			value = prms["value"]
		val = self.COMARtoCSLValue(value)		
		res = self.callPropertySet(name, index,  val)		
		if res == 1:
			return self.COMARValue.COMARRetVal(1, None)
		else:
			return self.COMARValue.COMARRetVal(0, None)

	def	runMethod(self, name = "__default", prms = {}):
		""" Called from COMAR Container/objhook. prms is COMARValue  """

		prms = self.CSLBuildPrmList(prms)
		localTbl = { 'vars':{}, 'status':0, 'props':{}, 'alias':{}, 'persistent':{}, 'instance':{}}

		res = self.callMethod(name, prms, localTbl)

		if localTbl["status"] == 2:
			return self.COMARValue.COMARRetVal(1, None)
		else:			
			ret = self.CSLtoCOMARValue(res)
			self.debug(DEBUG_FATAL, "RETS:", res, '(%s)->' % (res.type), ret)
			return self.COMARValue.COMARRetVal(0, ret)

	def runFunction(self, name = "__value", prms = {}):
		""" Called from COMAR Container/objhook. prms is COMARValue  """

		prms = self.CSLBuildPrmList(prms)
		localTbl = { 'vars':{}, 'status':0, 'props':{}, 'alias':{}, 'persistent':{}, 'instance':{}}

		res = self.callFunction(name, prms, localTbl)

		if localTbl["status"] == 2:
			return self.COMARValue.COMARRetVal(1, None)
		else:
			return self.COMARValue.COMARRetVal(0, self.CSLtoCOMARValue(res))

	def CSLCreateLocalTbl(self, prms = {}, prototype = {}, symtab = {}, persistent = [], instance = []):
		obj_desc = self.COMARAPI.createObjDesc(objType = "CSL:OMINSTANCE", instance = self.instance, ci = self.callerInfo)
		me_obj = CSLValue(typeid = "object", value = obj_desc)
		localTbl = { 'vars':{"me":me_obj}, 'status':0, 'props':{}, 'alias':{}, 'persistent':persistent, 'instance':instance }
		prmNames = prms.keys()
		ptbl = localTbl['vars']
		
		if 0:
			for key in symtab["vars"]:
				if prototype.has_key(key):
					val = symtab["vars"][key];
					if type(val) != type('') and type(val) != type(1) and val[0] == "$" and val[1] in "AQNIFO":
						val = self.CSLCheckVariable(val, symtab)
					localTbl["vars"][key] = val

		for key in prmNames:
			#print "CSE Parameter:", key, prms[key]
			if prototype.has_key(key):				
				val = prms[key] #self.CSLCheckVariable(prms[key], symtab)
				if type(val) == type('') and val[0] == "$" and (val[1] in "AQNIFO"):
					#print "VALUE GET:", val
					val = self.CSLCheckVariable(val, symtab)
				#print "ADD LOCALTBL:", key, val
				localTbl['vars'][key] = val
				del prototype[key]
			else:
				print "Undefined parameter:", key

		prmNames = prototype.keys()

		for key in prmNames:
			self.debug(DEBUG_CALL, 'Build key: "%s" from %s ' % (key, prmNames))
			if key != "":
				localTbl['vars'][key] = self.CSLCheckVariable(prototype[key], symtab)

		for key in persistent:
			if key != "":
				localTbl['vars'][key] = self.CSLPersistGet(key)
				self.debug(DEBUG_PRST,  "PERSIST_" , key, "=", ptbl[key])


		for key in instance:
			if key != "":
				ptbl[key] = self.CSLInstanceGet(key)
				self.debug(DEBUG_PRST, "INSTANCE_" , key, "=", ptbl[key])

		return localTbl

#----------------------------------------------------------------------------
# CAPI and CSL stdLib calls.
#----------------------------------------------------------------------------
	def CSLisCAPI(self, name=""):
		#print "CAPI:", self.CAPI, dir(self.CAPI)
		return self.CAPI.has_function(name)

	def CAPIFunc(self, name = "", prms = {}, symtab = {}):
		""" CAPI Processor. This is a really big function :( """
		prmkeys = prms.keys()
		for item in prmkeys:
			#print "item: %s -> %s" % (item, prms[item]) , " = ",
			prms[item] = self.CSLCheckVariable(id = prms[item], localTbl = symtab)
			#print prms[item]

		if name == "debugout":
			if prms.has_key("value") or prms.has_key("$__obj"):
				if prms.has_key("$__obj"):
					prms["value"] = prms["$__obj"]
				self.debugout(prms["value"])
				return None
				
		if self.cslAPIS.has_key(name):
			ret = self.cslAPIS[name](prms)
			if ret:
				return ret
			return CSLValue("NULL", None)
		# We not found name in CSL CAPI functions.
		# We try COMAR CAPI functions..

		if self.CSLisCAPI(name):
			# Yes, its defined with nsAPI CAPI entry..
			# First, create a COMARValue array for parameters..
			keys = prms.keys()
			keys.sort()
			callPrm = {}
			for key in keys:				
				callPrm[key] = self.CSLtoCOMARValue(prms[key])
			#print "Call CAPI:", name, callPrm
			ret = self.CAPI.call(method = name, prms = callPrm, callerInfo = self.callerInfo)
			#ret = self.CAPI.call(function=name, prmlist = callPrm)
			#print "CAPI Call:", name, ret.execResult, self.COMARValue.dump_value_xml(ret.returnValue)
			if ret.execResult:
				return CSLValue("NULL", None)
			else:
				return self.COMARtoCSLValue(ret.returnValue)

		return CSLValue("NULL", None)

	def	debugout(self, var = None, nest = 0):
		
		if var == None:
			return
		sp = '   ' * nest
		if var.type == 'array':

			print sp, "ARRAY-------------"
			if self.dbgf:
				self.dbgf.write(sp + "ARRAY-------------\n" )
			for i in var.value.keys():
				print sp, 'KEY:', i
				if self.dbgf:
					self.dbgf.write(sp+"key:"+str(i)+"\n")
				self.debugout(var.value[i], nest + 1)
		else:
			print sp, 'TYPE: %s VALUE: %s' % (var.type, var.value)
			if self.dbgf:
				self.dbgf.write(sp + 'TYPE: %s VALUE: %s' % (var.type, var.value) +"\n")

	def	call(self, name = "", prms = {}, symtab = {}):
		self.debug(DEBUG_CALL, "CALL:", name, prms)
		func = name
		if func.find(":") == -1 and func.find(".") == -1:
			# API/CAPI Function call..
			#print "API/CAPI CALL:", name, prms
			return self.CAPIFunc(name = name, prms = copy.copy(prms), symtab = symtab)
		else:
			if func.find(":") == -1:
				rootObj = func[:func.find(".")]
				if rootObj == "me":
					return self.callFunction(name = func[func.find(".")+1:], prms = prms, symtab = symtab)
				else:
					return self.callExtFunction(name = name, prms = prms, symtab = symtab)
			else:
				return self.callExtFunction(name = name, prms = prms, symtab = symtab)

#----------------------------------------------------------------------------
#	Internal calls for executing procedures.
#----------------------------------------------------------------------------
	def callMethod(self, name = "", prms = {}, symtab = {}):
		# First build prms..
		self.debug(DEBUG_CALL, "MCALL: %s ( %s )" % (name, prms))
		fn = "m_" + name
		if not self.vtbl.has_key(fn):
			print "Method Not Found in:", fn, self.vtbl.keys(), name, prms
			return CSLValue("NULL", None)

		treeEntry = self.vtbl[fn]
		fnparms = copy.copy(treeEntry.data['prmlist'])

		localTbl = self.CSLCreateLocalTbl(prms, fnparms, symtab)

		#FIX At This point, we load persistent and instance values..
		self.procStack.append(name)
		l = self.CSLInterpreter(treeEntry.child, localTbl)
		self.procStack.pop()

		#print "GetMethod:", l['status'], l

		if l['vars'] != None and l['vars'].has_key(name):
			print "return:", l['vars'][name], l['vars'][name].type, l['vars'][name].value
			return copy.deepcopy(l['vars'][name])
		else:
			return CSLValue(typeid = "NULL", value = None)

	def	callFunction(self, name = "", prms = {}, symtab = {}):
		self.debug(DEBUG_CALL, "FCALL ENTRY: %s ( %s )" % (name, prms))
		fn = "f_" + name
		if not self.vtbl.has_key(fn):
			return CSLValue("NULL", None)

		self.procStack.append(name)
		treeEntry = self.vtbl[fn]
		print "FCL: treeentry:", treeEntry, self.vtbl
		fnparms = copy.copy(treeEntry.data['prmlist'])

		localTbl = self.CSLCreateLocalTbl(prms, fnparms, symtab)

		#FIX At This point, we load persistent and instance values..

		l = self.CSLInterpreter(treeEntry.child, localTbl)['vars']
		self.procStack.pop()

		self.debug(DEBUG_CALL, "GetFunc:", l)

		if l != None and l.has_key(name):
			return copy.deepcopy(l[name])
		else:
			return CSLValue(typeid = "NULL", value = None)

	def callPropertyGet(self, name = "__value", index = None):
		""" Called from CSL Script prms is CSLValue  """

		if name == 'IID':
			return CSLValue(typeid = "string", value = self.callerInfo.IID)

		Entry = self.vtbl['p_' + name + "_get"]

		#localTbl = { 'vars':{}, 'status':0, 'props':{}, 'alias':{}, 'persistent':{}, 'instance':{}}

		propEntry = Entry.parent

		prmName = propEntry.data['prm']

		localTbl = self.CSLCreateLocalTbl({}, {}, {}, copy.copy(propEntry.data['persistent']), copy.copy(propEntry.data['instance']))

		if prmName != "":
			if index == None:
				default = propEntry.data['default']
				if default != "":
					default = self.CSLCheckValue(default, localTbl)
				else:
					default = CSLValue(typeid = "NULL", value = None)
			else:
				default = index

			localTbl['vars'][prmName] = default

		self.procStack.append('p_' + name + '_get')
		self.lastLTbl = self.CSLInterpreter(Entry.child, localTbl)
		self.procStack.pop()
		l = self.lastLTbl['vars']

		self.debug(DEBUG_CALL,  "\n\nGetProp result: (", name, ")", l, "haskey:", l.has_key(name))

		if l != None and l.has_key(name):
			self.debug(DEBUG_CALL, "Get Property return:", l[name])
			return copy.deepcopy(l[name])
		else:
			return CSLValue(typeid = "NULL", value = None)

	def callPropertySet(self, name = "__value", index = None, value = None):
		""" Set Property Entry. Called from CSL Script prms is CSLValue  """
		pname = 'p_' + name + "_set"
		if not self.vtbl.has_key(pname):
			return 1

		Entry = self.vtbl[pname]

		localTbl = { 'vars':{}, 'status':0, 'props':{}, 'alias':{}, 'persistent':{}, 'instance':{}}

		propEntry = Entry.parent

		prmName = propEntry.data['prm']

		if prmName != "":
			if index == None:
				default = propEntry.data['default']
				if default != "":
					default = self.CSLCheckValue(default, localTbl)
				else:
					default = CSLValue(typeid = "NULL", value = None)
			else:
				default = index

			localTbl['vars'][prmName] = default

		if value == None:
			value = CSLValue(typeid = "NULL", value = None)

		localTbl['vars'][name] = value

		self.push(localTbl)
		self.procStack.append(pname)
		l = self.CSLInterpreter(Entry.child, localTbl)['status']
		self.procStack.pop()
		self.pop()

		self.debug(DEBUG_CALL, "SetProp:", l)

		if l == 2:
			return 1
		else:
			return 0
#----------------------------------------------------------------------------
# External calls. This cllas direction CSL -> COMARd
#----------------------------------------------------------------------------
	def callExtMethod(self, name = "", prms = {}, localTbl = {}):
		plist = {}
		for i in prms.keys():
			plist[i] = self.CSLtoCOMARValue(self.CSLCheckVariable(prms[i], localTbl))

		self.debug(DEBUG_CALL, "ExtMethod:", name, prms, plist)
		rv = self.ExtObjCall(Type="method", name = name, index = None, prms = plist, value = None)
		return self.COMARtoCSLValue(rv)

	def	callExtPropertyGet(self, name = "", index = None):
		self.debug(DEBUG_CALL, "ExtPropertyGet:", name, index)
		return CSLValue("NULL", None)

	def	callExtPropertySet(self, name = "", index = None , localTbl = {}, value = None):
		self.debug(DEBUG_CALL, "ExtPropertySet:", name, index, value, localTbl)
		pass

	def objCall(self, obj = None, Type = "propertyget", name = "", prms = {}):
		# we must use self.extObjCall()
		# But currently don't know prms.
		print "Obj '%s' called for '%s %s' with %s" % (obj, Type, name, prms)
		return CSLValue(typeid = "NULL", value = None)

#-----------------------------------------------------------------
# Main VM
#-----------------------------------------------------------------

	def CSLInterpreterLet(self, tree, localTbl):
		varName = tree.data["id"]
		val = self.CSLCheckVariable(tree.data["exp"], localTbl)
		self.debug(DEBUG_LET, "EXP:", varName, "=", tree.data["exp"], "->", val.type)

		if varName[0:2] == '$A':
			cont 		= 1
			arrDesc 	= self.Tbl['A'][varName]
			arrIndexes 	= arrDesc['prmlist']
			arrId  		= arrDesc['id']
			#print "ARR INDEXES:", arrIndexes
			if localTbl['alias'].has_key(arrId):
				arrId = localTbl['alias'][arrId][:]

			if arrId.find(".") == -1 and arrId.find(':') == -1:	# Not a COMAR object call..
				if not localTbl['vars'].has_key(arrId):
					localTbl['vars'][arrId] = CSLValue(typeid='array', value = {})
					#DBG print "NEW ARR:", localTbl['vars'], arrId
				elif localTbl['vars'][arrId].type != 'array':
					localTbl['vars'][arrId] = CSLValue(typeid='array', value = {})

				if cont:
					array = localTbl['vars'][arrId]
					#newkey = ""

					maxa = len(arrIndexes) - 1
					x = 0
					for ai in arrIndexes:
						ai = self.CSLCheckVariable(ai, localTbl).toString()
						ai = arrkeyfix(ai)
						if x == maxa:
							key = ai
							break
						#print "MOVE ARR:",
						if not array.value.has_key(ai):
							#print "CREATE SUB ARR:", ai
							array.value[ai] =  CSLValue(typeid='array', value = {})

						array = array.value[ai]
						x += 1
						#inx = self.CSLCheckVariable(ai, localTbl)
						#newkey = newkey + "\\" + inx.toString()
					#newkey = newkey[1:]
					if array.value == None:
						array.type = "array"
						array.value = {}
					#print "SET ARR:[%s] = %s" % (key, val.value),  array, array.value

					array.value[key] = copy.deepcopy(val) #CSLValue(typeid = val.type, value = copy.deepcopy(val.value))
					#print "AFTER LET:", localTbl['vars'][arrId].value
					if arrId in localTbl['persistent']:
						self.CSLPersistSet(arrId, localTbl['vars'][arrId])
					elif arrId in localTbl['instance']:
						self.CSLInstanceSet(arrId, localTbl['vars'][arrId])

			else:	# a Object property
				if arrId.find(":") == -1:
					rootObj = arrId[:arrId.find(".")]
					if rootObj == "me":
						inx = self.CSLCheckVariable(arrIndexes[0], localTbl)
						self.callPropertySet(name = varName, index = inx, localTbl = localTbl, value = val)
						cont = 0
					else:
						inx = self.CSLCheckVariable(arrIndexes[0], localTbl)
						self.callExtPropertySet(name = varName, index = inx , localTbl = localTbl, value = val)
				else:
					inx = self.CSLCheckVariable(arrIndexes[0], localTbl)
					self.callExtPropertySet(name = varName, index = inx , localTbl = localTbl, value = val)

			del val
		else:
			if varName[0:1] == "$":
				varName = self.CSLCheckVariable(varName, localTbl)

			if localTbl['alias'].has_key(varName):
				varName = localTbl['alias'][varName]

			if varName.find(".") == -1 and varName.find(':')  == -1:
				if not localTbl["vars"].has_key(varName):
					self.debug(DEBUG_LET, "LET CREATE VAR:", varName, val.type, val.value, "TD:", tree.data["exp"])
					localTbl["vars"][varName] = None

				localTbl["vars"][varName] = copy.deepcopy(val)
				if 0:
					print varName,"=", tree.data["exp"], val.type, val.value,
					vk = localTbl["vars"].keys()
					vk.sort()
					for i in vk:
						print "%s -> %s " % (i, localTbl["vars"][i]()),
					print "\n"
				if varName in localTbl['persistent']:
					self.CSLPersistSet(varName, val)

				if varName in localTbl['instance']:
					self.CSLInstanceSet(varName, val)

				#print "LET ->", localTbl["vars"]
			else:	# A COMAR Property Call..
				self.callExtPropertySet(name = varName, index = None , localTbl = localTbl, value = val)

		return localTbl

	def	CSLInterpreter(self, startNode, localTbl = None, tnStack = None, opStack = None, contFrom = None):
		""" Main CSL Executor. Return Local Variable and status Table """
		#print "CSL Entry:", localTbl.keys(), localTbl['vars'].keys()
		tree = startNode
		if localTbl == None:
			localTbl = { 'vars':{}, 'status':0, 'props':{}, 'alias':{}, 'persistent':{}, 'instance':{}}
			for i in self.vtbl.keys():
				if i[0:2] == "p_":
					localTbl['props'][i[2:]] = self.vtbl[i]

		if tnStack == None:
			tnStack = []
		if opStack == None:
			opStack = []
		contLoop = 1

		while contLoop:
			#print "CONT:", tnStack #, opStack
			#self.saveMachineState(tree, localTbl, tnStack, opStack);
			if tree == None:
				if len(tnStack) == 0:
					contLoop = 0
			while tree != None:
				self.debug(DEBUG_TREE, "  " * len(tnStack), tree.type, tree.data, localTbl['status'])
				if tree.type == "LET":
					localTbl = self.CSLInterpreterLet(tree, localTbl)
					tree = tree.next

				elif tree.type == "CALL":
					m = tree.data['method']
					#print "CALL:", m, tree.data['prm']
					if m.find(":") == -1 and m.find(".") != -1:
						rootObj = m[:m.find(".")]
						fname   = m[m.find(".")+1:]
						#print "CALL ENTRY:", rootObj, fname
						if fname.find(".") == -1:							
							#print "CSLCV - FUNC CALLER:", f["id"], f["prmlist"]
							if rootObj == "me":
								tmp = self.callFunction(name = fname, prms = tree.data['prm'], symtab = localTbl)
							else:
								if localTbl['vars'].has_key(rootObj):
									obj = localTbl['vars'][rootObj]
									if obj.type == "object":
										tmp =  self.objCall(obj = obj, Type="method", name = fname, prms = tree.data['prm'])
									else:
										tree.data['prm']["$__obj"] = obj
										tmp = self.CAPIFunc(name = fname, prms = tree.data['prm'], symtab = localTbl)
					else:
						self.call(name = tree.data['method'], prms = tree.data['prm'], symtab = localTbl)
					tree = tree.next

				elif tree.type == "if":
					cnd = tree.data['cond']
					ifv = self.CSLCheckVariable(cnd, localTbl)
					tree.data['stat'] = ifv.toBoolean()
					if cnd[:2] == "$O":
						cnd = self.Tbl["O"][cnd]
					#print "IF Command:", tree.data, cnd, tree.data['stat'], ifv.type, ifv.value
					if tree.data['stat']:
						tnStack.append(tree.next)
						opStack.append({ 'op': 'if', 'loopBegin': tree.child })
						tree = tree.child
					else:
						tree = tree.next

				elif tree.type == "else":
					if tree.prev.data['stat'] == 0:
						tnStack.append(tree.next)
						opStack.append({ 'op': 'else', 'loopBegin': tree.child })
						tree.prev.data['stat'] == 1
						tree = tree.child
					else:
						tree = tree.next

				elif tree.type == "elif":
					if tree.prev.data['stat'] == 0:
						tree.data['stat'] = self.CSLCheckVariable(tree.data["cond"], localTbl).toBoolean()
						if tree.data['stat']:
							tree.prev.data['stat'] == 1
							opStack.append({ 'op': 'elif', 'loopBegin': tree.child })
							tnStack.append(tree.next)
							tree = tree.child
						else:
							tree = tree.next
					else:
						tree.data['stat'] = 0
						tree = tree.next

				elif tree.type == "while":
					wcond = copy.deepcopy(tree.data['cond'])
						#tree.data['stat'] = self.CSLCheckVariable(wcond, localTbl).toBoolean()
						#if not tree.data['stat']:
						#	break
					tree.data['stat'] = self.CSLCheckVariable(tree.data["cond"], localTbl).toBoolean()
					#self.debug(DEBUG_FATAL, "While entry:", tree.data)
					if tree.data['stat']:
						tnStack.append(tree.next)
						opStack.append({ 'cond': wcond, 'op': 'while', 'loopBegin': tree.child })
						#self.debug(DEBUG_FATAL, "While loop data:", tree.data)
							#localTbl = self.CSLInterpreter(tree.child, localTbl)
						tree = tree.child
					else:
						tree = tree.next

				elif tree.type == "for":
					fstart = copy.deepcopy(tree.data['start'])
					foper  = copy.deepcopy(tree.data['oper'])
					#print "C:" , tree.child, "N:", tree.child.next
					fcond  = tree.data['cond']

					if fstart.type == 'LET':
						localTbl = self.CSLInterpreterLet(fstart, localTbl)
					else:
						localTbl = self.CSLInterpreter(fstart, localTbl)

					wcond = copy.deepcopy(fcond)
					tree.data['stat'] = self.CSLCheckVariable(wcond, localTbl).toBoolean()
					if not tree.data['stat']:
							# for condition is true, cannot process for tree
						localTbl['status'] = 0
						tree = tree.next
					else:
						opStack.append({ 'op':'for', 'data':tree.data, 'loopBegin': tree.child })
						tnStack.append(tree.next)
						tree = tree.child

				elif tree.type == "makeinstance":
					self.debug(DEBUG_PRST, "MAKE INSTANCE:", tree.data)
					newvar = tree.data['objname']
					newid  = self.CSLCheckVariable(tree.data['objid']).toString()
					localTbl['vars'][newvar] = self.nsAPI.makeinstance(newid)					
					self.debug(DEBUG_FATAL, "new instance:", newvar)
					self.debug(DEBUG_FATAL, "opaque data:", localTbl['vars'][newvar].value)
					tree = tree.next

				elif tree.type == "persistent":
					for v in tree.data['variables']:
						p = self.CSLPersistGet(v)
						#print "SET:", v, "for:", localTbl['persistent']
						if p != None:
							localTbl['vars'][v] = p
							if not v in localTbl['persistent']:
								localTbl['persistent'].append(v)

							#print 'VAR:', v, "->", p.toString()
						else:
							localTbl['vars'][v] = CSLValue(typeid = "auto", value = "")
							if not v in localTbl['persistent']:
								localTbl['persistent'].append(v)

							#print 'VAR:', v, "-> null"
					tree = tree.next

				elif tree.type == "instance":
					# Persistent vars always save with LET Operation..
					#print "INSTANCE VARS:", tree.data
					for v in tree.data['variables']:
						p = self.CSLInstanceGet(v)
						#print "SET:", v, "for:", localTbl['instance']
						if p != None:
							localTbl['vars'][v] = p
							if not v in localTbl['instance']:
								localTbl['instance'].append(v)
							#print 'VAR:', v, "->", p.toString()
						else:
							localTbl['vars'][v] = CSLValue(typeid = "auto", value = "")
							if not v in localTbl['instance']:
								localTbl['instance'].append(v)

							#print 'VAR:', v, "-> null"

					tree = tree.next

				elif tree.type == "destroy":
					tree = tree.next
				elif tree.type == "delete":
					v = tree.data['var']
					if v[:2] == "$A":
						p = self.Tbl['A'][v]
						#print "Delete:", p
						i = p["id"]
						if localTbl['vars'].has_key(i):
							v = localTbl['vars'][i]
							ls = ""							
							if v.type == "array":
								a = v.value
								#print "Delete item:", v, a, i, p["prmlist"]
								x = 0
								mx = len(p["prmlist"]) - 1
								for k in p["prmlist"]:								
									l = self.CSLCheckVariable(k, localTbl)
									lv = l.toString()
									lv = arrkeyfix(lv)
									if a.has_key(lv):
										if x == mx:
											# Delete Point:
											del a[lv]
										else:
											a = a[lv].value
									x += 1	
								if i in localTbl['persistent']:
									self.CSLPersistSet(i, localTbl['vars'][i])
								elif i in localTbl['instance']:
									self.CSLInstanceSet(i, localTbl['vars'][i])
							else:
								del localTbl['vars'][i]

					tree = tree.next
				elif tree.type == "foreach":
					valuevar = tree.data['value']
					keyvar = tree.data['keyid']
					instvar = tree.data['instance']
					va = tree.data['array']
					if localTbl['vars'].has_key(va):
						#print "LOCALS:", localTbl['vars'],
						if localTbl['vars'][va].type != 'array':
							self.debug(DEBUG_TREE, "RAW VA:", va, localTbl['vars'][va].type, localTbl['vars'][va].value)
							ava = localTbl['vars'][va]
							va = { '0': CSLValue(typeid = ava.type, value = copy.deepcopy(ava.value)) }
						else:
							va = localTbl['vars'][va].value
						self.debug(DEBUG_TREE, "VA:", va)
						inxs = va.keys()
						if len(inxs):
							inxs.sort()
							if tree.data['rev']:
								inxs.reverse()							
							localTbl['status'] = 0
							op = { 'op':'foreach', 'data':tree.data, 'loopBegin': tree.child,
											'curinx': 0, 'index' : inxs,
											'vars':va, 'key': keyvar, 'val':valuevar }

							localTbl['vars'][op['key']] = CSLValue(typeid = 'string', value=op['index'][op['curinx']])
							localTbl['vars'][op['val']] = op['vars'][op['index'][op['curinx']]]
							# Continue loop..

							#print "FOREACH KEY(%s): '%s' VAL(%s):'%s'" % (op['key'], localTbl['vars'][op['key']].toString(), op['val'], localTbl['vars'][op['val']].toString() )
							#print "FOREACH KEYS:", inxs, "NEXT:", tree.next
							#op['curinx'] += 1
							op['curinx'] = 0


							opStack.append(op)
							tnStack.append(tree.next)
							tree = op['loopBegin']
							tree = tree.child
						else:
							tree = tree.next
					else:
						tree = tree.next

				elif tree.type == "break":
					localTbl['status'] = 1
					break

				elif tree.type == "abort":
					localTbl['status'] = 2
					break

				elif tree.type == "continue":
					localTbl['status'] = -1
					break

				else:
					#if tree.next == None:
						#print "SM Exit @ ", tree.codeLine, "=", tree.type
					tree = tree.next

				# State Machine Loop....
			#print "SM Exit @ ", tree, localTbl['status']

			if localTbl['status'] == -1 or tree == None:
				# PASS/Continue. GO last tree Item
				sp = len(opStack) - 1
				bp = len(tnStack) - 1
				#print "SP/BP:", sp, bp
				if sp > -1:
					op = opStack[sp]
					oper = op['op']
				#print oper, '->',op
				if (bp < 0):
					#print "Normal program termination: ", localTbl['vars']
					contLoop = 0
				elif oper == 'if':
					tree = opStack.pop()
					tree = tnStack.pop()
					#print "IF", "=", tree.codeLine, ":", tree.type
				elif oper == 'elif':
					tree = opStack.pop()
					tree = tnStack.pop()
				elif oper == 'else':
					tree = opStack.pop()
					tree = tnStack.pop()
				else:
					#JMP loop start instruction..
					# Check condition if avail..
					if oper == "while":
						# Check condition from 'cond'
						#self.debug(DEBUG_FATAL, "While:", op)
						wcond = op['cond']
						stat = self.CSLCheckVariable(wcond, localTbl).toBoolean()
						if stat:
							tree = op['loopBegin']
						else:
							tree = tnStack.pop()
							stat = opStack.pop() # Temporary variable..

					elif oper == "for":
						# Execute loop variable..
						localTbl = self.CSLInterpreter(op['data']['oper'], localTbl)
						if self.CSLCheckVariable(op['data']['cond'], localTbl).toBoolean():
							# Continue loop..
							tree = op['loopBegin']
						else:
							# exit loop
							tree = tnStack.pop()
							stat = opStack.pop() # Temporary variable..

					elif oper == "foreach":
						#localTbl = self.CSLInterpreter(op['data']['oper'], localTbl)
						#print "foreach", op['curinx'], op['index']
						if len(op['index']) > (op['curinx']):
							localTbl['vars'][op['key']] = CSLValue(typeid = 'string', value=op['index'][op['curinx']])
							localTbl['vars'][op['val']] = op['vars'][op['index'][op['curinx']]]

							# Continue loop..
							#print "FOREACH KEY(%s): '%s' VAL(%s):'%s'" % (op['key'], localTbl['vars'][op['key']].toString(), op['val'], localTbl['vars'][op['val']].toString() )

							tree = op['loopBegin']
							#print "BEGIN:", tree, tree.type, "tnstack:", tnStack[-1]
							op['curinx'] += 1

						else:
							# exit loop
							tree = tnStack.pop()
							stat = opStack.pop() # Temporary variable..													
							#print "END:", tree
					else:
						tree = tnStack.pop()
						stat = opStack.pop()

			elif localTbl['status'] == 1:
				# return previous level
				if len(tnStack):
					tree = tnStack.pop()
					stat = opStack.pop()
				else:
					contLoop = 0
				pass

			elif localTbl['status'] == 2:
				# immediately exit with abort.
				contLoop = 0

			# Main Loop
		return localTbl

	def CSLEvalExp(self, exp = "", localTbl = None):	# $O Handler..
		# Expression eval..
		tbl = exp[1:2]

		oper = self.Tbl[tbl][exp]
		#print "EVAL:", exp, "->", oper
		# '$O4': {'src': '$I3', 'dst': '$I2', 'op': '=='}
		op  = oper["op"]
		src = self.CSLCheckVariable(oper['dst'], localTbl)
		dst = self.CSLCheckVariable(oper['src'], localTbl)
		self.debug(DEBUG_EXP, "EVAL src: %s = '%s' (%s) dst: %s = %s (%s)" % (oper['dst'],src.value, src.type, oper['src'], dst.value, dst.type))
		if   op == "+":
			res = src.op.op_add(dst)
		elif op == "-":
			res = src.op.op_del(dst)
		elif op == "*":
			res = src.op.op_mul(dst)
		elif op == "/":
			res = src.op.op_div(dst)
		elif op == "^":
			res = src.op.op_exp(dst)
		elif op == "%":
			res = src.op.op_mod(dst)
		elif op == "==":
			res = src.op.op_equ(dst)
		elif op == "!=":
			res = not src.op.op_equ(dst)
		elif op == ">=":
			res = src.op.op_gte(dst)
		elif op == "<=":
			res = src.op.op_lte(dst)
		elif op == ">":
			res = src.op.op_gt(dst)
		elif op == "<":
			res = src.op.op_lt(dst)
		elif op == "&&":
			res = src.op.op_and(dst)
		elif op == "||":
			res = src.op.op_or(dst)

		if type(res) is types.BooleanType:
			res = int(res)

		res = CSLValue(typeid = src.type, value = res)

		return res

	def CSLCheckVariable(self, id = "", localTbl = None):
		#print "check variable:", id
		if id == None:
			self.debug(DEBUG_FATAL, "Invalid entry !")
			self.printTreeNode(self.root)
			return CSLValue("NULL", None)
		if isinstance(id, CSLValue):
			return id
		if id[0:2] == "$A":
			# array or property value..
			if id.find(".") != -1:
				methodPart = id[id.find(".")+1:]
				#id = id[:id.find(".")]
			else:
				methodPart = None
			a = self.Tbl['A'][id]['id']
			if a[0:2] == '$A':
				a = self.Tbl['A'][a]['id']
				inx = self.Tbl['A'][a]['prmlist'][0]
				if inx[0] == "$":
					inx = CSLCheckVariable(inx, localTbl)
				a = a + "[" + inx + "]"

			if a[0] != '$':
				if not localTbl["vars"].has_key(a):
					# identifier not defined as local var.
					if not localTbl['props'].has_key(a + "_get"):
						if a.find(".") == -1 and a.find(":") == -1:
							# not a property..

							localTbl['vars'][a] = CSLValue(typeid='array', value = {})
						else:
							# check self call:
							rootObj = a[:a.find(".")]
							if rootObj == "me":
								ret = self.callPropertyGet(name = a[a.find(".") + 1:], index = None)
								return ret
							elif localTbl['vars'].has_key(rootObj):
								# This is a temporary object
								# rootObj.value always a COMARObjectDescriptor..
								obj = localTbl['vars'][rootObj]
								if obj.type == "object":								
									return self.objCall(obj = obj, Type = "propertyget", name = a, prms = self.Tbl['A'][id]['prmlist'])
								else:
									# We are require many special cases...
									pass
							if methodName:
								a = a + "[" + arrkeyfix(self.Tbl['A'][id]['prmlist'][0]) + "]." + methodName
								ret = self.callExtPropertyGet(name = a, index = arrkeyfix(self.Tbl['A'][id]['prmlist'][0]))
							else:
								ret = self.callExtPropertyGet(name = a, index = arrkeyfix(self.Tbl['A'][id]['prmlist'][0]))
							return ret
					else:
						ret = self.callPropertyGet(name = a, index = self.Tbl['A'][id]['prmlist'][0])
						return ret
				if len(self.Tbl['A'][id]['prmlist']):
					arrIndexes 	= self.Tbl['A'][id]['prmlist']
					array = localTbl['vars'][a]
					if array != None and array.type != "array":
						return CSLValue("NULL", None)
					maxa = len(arrIndexes) - 1
					x = 0
					#print "CSL Array Search:", arrIndexes, array
					for ai in arrIndexes:
						ai = self.CSLCheckVariable(ai, localTbl).toString()
						ai = arrkeyfix(ai)
						if x == maxa:
							key = ai
							break
						#print "MOVE ARR:", array, ai
						if not haskey(array.value, ai):
							#print "CREATE SUB ARR:", ai
							if array == None:
								array = CSLValue(typeid='array', value = {})
							array.value[ai] =  CSLValue(typeid='array', value = {})
						array = array.value[ai]
						x += 1
					#print "ARRAY LOOKUP:", key, type(key), "->", array.value, haskey(array.value, key)
					if not haskey(array.value, key):
						array.value[key] = CSLValue("NULL", None)
					try:
						arr = array.value[key]
					except:
						if type(key) == type(""):
							arr = array.value[int(key)]
						else:
							arr = array.value[str(key)]
					#print "GET ARR:", arr
					return arr
				return localTbl['vars'][a]

		if id[0:2] == "$I":
			a = self.Tbl['I'][id]
			if a[0] != '$':
				if not localTbl["vars"].has_key(a) :
					#FIXT: if not localTbl['props'].has_key(a + "_get"):
					if a.find(".") == -1 and a.find(":") == -1:
						#print "VAR CREATION:", a
						localTbl['vars'][a] = CSLValue("NULL", None)
					else:
						rootObj = a[:a.find(".")]
						if rootObj == "me":
							ret = self.callPropertyGet(name = a[a.find(".") + 1:], index = None)
							return ret
						elif localTbl["vars"].has_key(a):	# Locally defined object ?
							if localTbl["vars"][a].type == "object":
								# Hugh.. Its a object call
								# FIX ME P:1
								obj = localTbl['vars'][a]
								a = a + "._default"
								return self.objCall(obj = obj, Type="propertyget", name = a, prms = {})
								pass
						else:
							ret = self.callExtPropertyGet(name = a, index = None)
							return ret

				ret = localTbl['vars'][a]
				#if type(ret) == type("") and ret[0] == "$" and ret[1] in "N" and ret[2] in "0123456789":
				#	ret = self.CSLCheckVariable(ret, localTbl)
				#print "L['vars'][a]:", ret, "->", localTbl['vars']
				if ret.type == "NULL" and ret.value != None:
					try:
						r = float(ret.value)
						ret = CSLValue("numeric", ret.value)
						localTbl['vars'][a] = ret
					except:
						ret = CSLValue("string", ret.value)
						localTbl['vars'][a] = ret

				return ret
			else:
				return self.CSLCheckVariable(a, localTbl)

		if id[0:2] == "$O":
			#return CSLValue(typeid = "auto", value = self.CSLEvalExp(id, localTbl).value)
			return self.CSLEvalExp(id, localTbl) #.value

		if id[0:2] == "$N":
			return CSLValue(typeid = "numeric", value = float(self.Tbl['N'][id]))

		if id[0:2] == "$F":
			# A Function call.
			# Seek object function table first..
			f = self.Tbl['F'][id]
			#print "CSLCV - FUNC CALLER:", f["id"], f["prmlist"]
			func = f["id"]
			if func.find(":") == -1 and func.find(".") == -1:
				# API/CAPI Function call..
				return self.CAPIFunc(name = func, prms = copy.copy(f["prmlist"]), symtab = localTbl)
			else:
				if func.find(":") == -1:
					rootObj = func[:func.find(".")]
					if rootObj == "me":
						#print "ME.FuncCall - ", func, func[func.find(".")+1:], f["prmlist"]
						return self.callFunction(name = func[func.find(".")+1:], prms = f["prmlist"], symtab = localTbl)
					else:
						obj = None
						if rootObj[0] == "$":
							obj = self.CSLCheckVariable(rootObj, localTbl)
							
						if obj != None or localTbl['vars'].has_key(rootObj):
							# This is a temporary object
							# rootObj.value always a COMARObjectDescriptor..
							if obj == None: 
								obj = localTbl['vars'][rootObj]
							if obj.type == "object":
								return self.objCall(obj = obj, Type="method", name = func, prms = f['prmlist'])
							else:
								f["prmlist"]["$__obj"] = obj
								name = func[func.find(".")+1:]
								if name.find(".") == -1:
									return self.CAPIFunc(name=name, prms = copy.copy(f["prmlist"]), symtab = localTbl)
								else:
									return self.objCall(obj = obj, Type="method", name = func, prms = f['prmlist'])
						else:
							return self.callExtMethod(name = func, prms = f["prmlist"], localTbl = localTbl)
				else:
					#callExtMethod(name = "", prms = {}, localTbl = {}):
					return self.callExtMethod(name = func, prms = f["prmlist"], localTbl = localTbl)

		if id[0:2] == "$Q":
			#print "STRING REQUEST:", id, "->", self.Tbl['Q'][id]
			return CSLValue(typeid = "string", value = self.Tbl['Q'][id])

		if localTbl["vars"].has_key(id) == -1:
				localTbl['vars'][id] = CSLValue("NULL", None)

		#print "ID: %s Value: %s" % (id, localTbl['vars'][id].value)
		return localTbl['vars'][id]

#-------------------------------------------------------------------
# CSLValue handling.
#-------------------------------------------------------------------
class CSLValue:
	""" CSL Value type.
	CSL Value, define basic data types, numeric, integer and boolean.
	For object types,
	"""
	def	__init__(self, typeid = "auto", value = None, persist = 0, instance = 0):
		if typeid == "auto":
			if type(value) in [ types.IntType, types.FloatType, types.LongType ]:
				typeid = "numeric"
			elif type(typeid) == types.StringType:
				typeid = "string"
			else:
				typeid = "string"
				value = value.__str__()

		self.type = typeid
		self.value = value
		self.attrPersist = persist
		self.attrInstance = instance
		self.array	= None
		if typeid == "string":
			self.op = CSLTmpString(value)
			if type(value) in [ types.IntType, types.FloatType, types.LongType ]:
				self.value = value.__str__()
			elif type(value) is types.BooleanType:
				self.value = "y"

		elif typeid == "numeric":
			self.op = CSLTmpNumeric(value)
			self.value = value
		elif typeid == "object":
			self.op = None
			self.value = value
		elif typeid == "boolean":
			value = int(value != 0)
			self.value = value
			self.op = CSLTmpNumeric(value)
		else:
			self.op = CSLTmpString("")
			self.value = value

	def	toComar(self, nsAPI):
		if self.type == "string":
			return nsAPI.COMARValue.string_create(cslVal.toString())

		elif self.type == "numeric" or cslVal.type == "boolean":
			return nsAPI.COMARValue.numeric_create(cslVal.value)
			#return self.COMARValue.COMARValue(type = "numeric", data = cslVal.value)

		elif self.type == "array":
			arr = nsAPI.COMARValue.array_create()
			for key in self.value.keys():
				nsAPI.COMARValue.array_additem(arr, key, 0, self.value[key].toComar())
			return arr

	def __call__(self, type = ""):
		if type == "string":
			return self.toString()

		if type == "numeric":
			return self.toNumeric()

		if type == "boolean":
			return self.toBoolean()

		return self.value

	def	toNumeric(self):
		if self.type == "string":
			try:
				return float(self.value) # == int(self.value):
			except:
				return 0
		elif self.type == "numeric":
			return float(self.value)
		elif self.type == "object":
			if value != None:
				pass
		elif self.type == "array":
			pass
		elif self.type == "boolean":
			return self.value
		else:
			return 0

	def	toString(self):
		if self.type == "string":			
			return self.value
		elif self.type == "numeric":
			return str(self.value)
		elif self.type == "object":
			if value != None:
				pass
		elif self.type == "array":
			pass
			
		elif self.type == "boolean":
			if self.value:
				return "Y"
			else:
				return "N"
		else:
			return ""

	def	toBoolean(self):
		""" TODO: Language Specific "Yes" implementation """
		if self.type == "string":
			if self.value == "Y" or  self.value == "y" or self.value.upper() == "YES":
			   return 1
			else:
				try:
					r = int(self.value)
					if r != 0:
						r = 1
				except:
					r = 0
				return r
			return self.value

		elif self.type == "numeric":
			try:
				return int(self.value) != 0
			except:
				return 0

		elif self.type == "object":
			if value != None:
				return 1

		elif self.type == "array":
			return self.value != None

		elif self.type == "boolean":
			return self.value != 0

		else:
			return 0

class CSLTmpString:
	def	__init__(self, strval):
		self.val = strval

	def op_add(self, valObj):
		tmp = valObj.toString()		
		#print "OP_ADD:", self.val, tmp
		return str(self.val) + tmp

	def op_del(self, valObj): # Oopps !
		return ""

	def op_mul(self, valObj):
		if valObj.type == "numeric":
			ret = ""
			for i in xrange(valObj.value):
				ret += self.val
			return ret
		return ""

	def op_div(self, valObj):
		return ""

	def op_exp(self, valObj):
		return ""

	def op_mod(self, valObj):
		return ""

	def op_equ(self, valObj):
		tmp = valObj.toString()
		return self.val == tmp

	def op_gt(self, valObj):
		tmp = valObj.toString()
		return self.val > tmp

	def op_lt(self, valObj):
		tmp = valObj.toString()
		return self.val < tmp

	def op_gte(self, valObj):
		tmp = valObj.toString()
		return self.val >= tmp

	def op_lte(self, valObj):
		tmp = valObj.toString()
		return self.val <= tmp
		
	def  op_or(self, valObj):
		tmp = valObj.toString()
		if self.val != "" or tmp != "":
			return "y"
		else:
			return "n"
			
	def  op_and(self, valObj):
		tmp = valObj.toString()
		if self.val != "" and tmp != "":
			return "y"
		else:
			return "n"

class CSLTmpNumeric:
	def	__init__(self, numval):
		self.val = float(numval)

	def op_add(self, valObj):
		tmp = valObj.toNumeric()
		#print self.val, tmp, type(self.val), type(tmp)
		return float(self.val) + tmp

	def op_del(self, valObj): # Oopps !
		tmp = valObj.toNumeric()
		return float(self.val) - tmp

	def op_mul(self, valObj):
		if valObj.type == "numeric":
			return float(valObj.value) * float(self.val)

		return 0

	def op_div(self, valObj):
		if valObj.type == "numeric":
			if valObj.value == 0:
				return 2^31
			return float(self.val) / float(valObj.value)

		return 0
	def op_exp(self, valObj):
		if valObj.type == "numeric":
			return self.val ** valObj.value

		return 1

	def op_mod(self, valObj):
		if valObj.type == "numeric":
			return self.val % valObj.value
		return self.val

	def op_equ(self, valObj):
		tmp = valObj.toNumeric()
		return self.val == tmp

	def  op_gt(self, valObj):
		tmp = valObj.toNumeric()
		return self.val > tmp

	def  op_lt(self, valObj):
		tmp = valObj.toNumeric()
		return self.val < tmp

	def  op_gte(self, valObj):
		tmp = valObj.toNumeric()
		return self.val >= tmp

	def  op_lte(self, valObj):
		tmp = valObj.toNumeric()
		return self.val <= tmp

	def  op_or(self, valObj):
		tmp = valObj.toNumeric()
		return self.val | tmp
	
	def  op_and(self, valObj):
		tmp = valObj.toNumeric()
		return self.val & tmp
	

class CSLArrayItem:
	def	__init__(self, Array=None, key=None, instance=0):
		if key == None:
			return None

		self.parent = Array
		self.key = key
		self.instance = instance
		self.value = None
		self.next = None
		self.prev = None
		self.child = None

def CheckParameters(capsule, method = "", prms = {}):
	"""
		prms icindeki parametrelerden kacinin bu method
		tarafindan kullanilabildigini tespit eder.
		alias olarak yapilmis tariflerde teste tabidir..
	"""
	if method == "":
		return -1

	try:
		tree = capsule.root.child
	except:
		return -1

	item = 0

	while tree != None:
		if tree.type == "defmethod" and tree.data["name"] == method:
			print "LOOK METHOD:", tree.data
			for i in prms.keys():
				print "    LOOK PRM:", i
				if i in tree.data["prmlist"]:
					item += 1
				else:
					if tree.data.has_key("alias"):
						aliased_prms = tree.data["alias"].keys()
						print "       LOOK ALIAS:", aliased_prms
						for x in aliased_prms:
							print "              LOOK IS:", x, i
							if i in tree.data["alias"][x]:
								item += 1

		tree = tree.next
	return item
#-------------------------------------------------------------------
# STD OBJHOOK
#-------------------------------------------------------------------
class	COMARObjHook:
	useContainer = True
	canPersist   = True
	def	__init__(self, cAPI = None, callerInfo = None, chldHelper = None, OMData = None):
		#" cAPI, a set of API's for CSL Library functions, COMARValue, COMARValue etc.
		# callerInfo contains, caller user, caller object, IID for Code, OID for code."
		if cAPI == None:
			self.objHandlers = { "CSL:ALL":self.objHandle, "CSL:OMINSTANCE":self.omInsHandle }
		else:
			self.file = ''
			cAPI.makeinstance = self.makeinstance
			print 'FILE:', __file__, "called.."
			self.procHelper = chldHelper
			self.runenv = None
			self.api 	= cAPI.IAPI		# COMARAPI
			#print dir(self.api)
			self.cv		= cAPI.COMARValue
			self.cAPI	= cAPI
			self.callerInfo = callerInfo
			self.instance = None
			self.instanceid = "" #instanceid
			self.omdata = OMData
			#print "CSLRunEnv CAPI Info:"
			#for i in dir(cAPI):
			#	x = getattr(cAPI, i)
			#	print i,"=", x
		print "CSLRunEnv Caller Info:"
		for i in dir(callerInfo):
			x = getattr(callerInfo, i)
			print i,"=", x

	def loadInstance(self, instanceid = ""):
		self.instance = self.api.loadValue(instanceid, 'hookdata', self.callerInfo)
		#nsAPI = None, extObjEntry = None, callerInfo = None):
		self.runenv = CSLCapsule(instance=instanceid, nsAPI=self.cAPI, extObjEntry = self.extCall, callerInfo=self.callerInfo)
		print "CSLRunEnv LoadInstance:", instanceid, self.instance, self.cv.gettype(self.instance), self.callerInfo.mode
		if self.cv.gettype(self.instance) != 'null':
			if self.callerInfo.mode == "auto":
				# This is a new instance..
				# Make our instance data..
				codetype = self.cv.array_finditem(self.instance, 'code_type')
				print "CSLRunEnv: LoadInstance:", self.cv.dump_value_xml(codetype.item), self.instance
				if codetype.item.data.value == 'file':
					cslfile = self.cv.array_finditem(self.instance, 'source')
					self.runenv.LoadObject(cslfile.item.data.value)
				elif codetype.item.data.value == 'db_key':
					cslfile = self.cv.array_finditem(self.instance, 'db_file')
					key = self.cv.array_finditem(self.instance, 'db_key')
					db = self.procHelper.dbOpen(cslfile.item.data.value)
					print "CSLRunEnv: Try load code tree:", cslfile.item.data.value, db, key.item.data.value
					tree = self.procHelper.dbRead(int(db), key.item.data.value)
					tree = gzip.zlib.decompress(tree)
					self.procHelper.dbClose(db)
					if tree:
						self.runenv.loadPreCompiled(tree)
						#self.runenv.printTree()
				else:
					if callerInfo.mode == "tmp":
						cslcode = self.cv.array_finditem(self.instance, 'code_buffer')
						self.runenv.LoadBuffer(cslcode.item.data.value)
			elif self.callerInfo.mode == "tmp":
				pass
		else:
			self.cv.CVAL_destroy(self.instance)
			self.instance = self.cv.array_create()
			self.cv.array_additem(self.instance, 'code_type', 0, self.cv.string_create(str='null'))
			self.cv.array_additem(self.instance, 'source', 0, self.cv.string_create(str='null'))

		self.instanceid = instanceid
#--------------------------------------------------------------------------
# OM-DRIVER Specific Functions..
#--------------------------------------------------------------------------
	def	setSourceFromDBKey(self, dbfile = "",  key = ''):
		self.cv.CVAL_destroy(self.instance)
		self.instance = self.cv.array_create()
		self.cv.array_additem(self.instance, 'code_type', 0, self.cv.string_create(str='db_key'))
		self.cv.array_additem(self.instance, 'db_key', 0, self.cv.string_create(str=key))
		self.cv.array_additem(self.instance, 'db_file', 0, self.cv.string_create(str=dbfile))
		self.api.saveValue(self.instanceid, self.instance, 'hookdata', self.callerInfo)
		db = self.procHelper.dbOpen(dbfile)
		tree = self.procHelper.dbRead(db, key)
		if tree:
			tree = gzip.zlib.decompress(tree)
			self.procHelper.dbClose(db)
			if tree:
				self.runenv.loadPreCompiled(tree)
		else:
			print "CSLRunEnv: DBKEY/DBFILE Invalid :", dbfile, key

	def	setSourceFromURL(self, src = ''):
		url = urlparse.urlparse(src)
		proto = url[0]
		#print "proto:", proto
		if proto == 'file':
			self.file = url[2]
			self.cv.CVAL_destroy(self.instance)
			self.instance = self.cv.array_create()
			self.cv.array_additem(self.instance, 'code_type', 0, self.cv.string_create(str='url'))
			self.cv.array_additem(self.instance, 'url', 0, self.cv.string_create(str=self.file))
			self.api.saveValue(self.instanceid, self.instance, 'hookdata', self.callerInfo)
			self.runenv.LoadObject(self.file)
		else:
			# We must use COMAR URL Functions for retrieve URL data.
			# But, currently this is not ready..
			pass

	def	setSourceFromBuffer(self, buffer = ''):
		self.cv.CVAL_destroy(self.instance)
		self.instance = self.cv.array_create()
		self.cv.array_additem(self.instance, 'code_type', 0, self.cv.string_create(str='buffer'))
		self.api.saveValue(self.instanceid, self.instance, 'hookdata', self.callerInfo)
		#print "Compile Buffer:", buffer
		self.runenv.LoadBuffer(codeBuffer = buffer)

	def	compile(self, buffer):
		self.setSourceFromBuffer(buffer)
		return self.runenv.compileResult()

	def objHandle(self, objid = "", callType = "", callName = "", prms = {}, callerInfo = None):		
		pass

	def omInsHandle(self, objid = "", callType = "", callName = "", prms = {}, callerInfo = None):
		
		prm = self._buildPrms(prms)
		if callType == "method":
			res = self.runenv.runMethod( name, prm )
			return res
		else:
			if callType == "propertyget":				
				res = self.runenv.runPropertyGet( name, prm )
				return res
			if callType == "propertyset":
				prms = self._buildPrms(prmList)
				res = self.runenv.runPropertySet( property, prm, newValue )

	def	_buildPrms(self, prmList):
		prms = {}
		if prmList != None:
			for i in prmList.keys():
				prms[i] = prmList[i]
		#else:
		#	prms = None
		return prms
	# CSL to COMAR Calls.
	def	_tocomar(self, prmlist):
		if prmlist == None:
			return None
		arr = self.cv.array_create()
		for itemkey in prmlist.keys():
			comarval = self.runenv.CSLtoCOMARValue(prmlist[itemkey].toComar)
			self.cv.array_additem(key = itemkey, value = comarval)
		return arr

	def	_getcallpart(self, call=''):
		return call[call.find('.')+1:]

	def extCall(self, Type="", name = "", index = None, prms = {}, value = None):
		print "CH EXTCALL:", prms
		rpc = RPCData.RPCStruct()
		rpc.TTSID = ""
		rpc.makeRPCData("OMCALL")
		rpc["type"] = Type
		rpc["name"] = name
		if Type == "method":
			for p in prms.keys():
				v = self.cv.dump_value_xml(prms[p])
				v = v[v.find("\n")+1:]
				print "CSL->COMAR PRM:", p, v
				rpc.addPropertyMulti("parameter", p, prms[p])
		else:
			rpc.addPropertyMulti("parameter", "index", index)
			if Type == "propertyset":
				rpc.addPropertyMulti("parameter", "value", value)

		print os.getpid(), self.procHelper.modName, self.procHelper.myPID, "CSLOBJHOOK CALL INFO:", rpc["name"]
		self.procHelper.sendParentCommand("TRSU_OMC", self.procHelper.myPID, 0, rpc.toString())
		while 1:
			c = self.procHelper.waitForParentCmd(5)
			if c:
				cmd = self.procHelper.getParentCommand()
				print "CSL RUNENV: Parent returned:", cmd
				command = cmd[2]
				data = cmd[3]
				if command == "TRTU_TAE":
					st = int(data[:data.find(" ")])
					if st == 0:
						val = self.cv.load_value_xml(data[data.find(" ")+1:])
					else:
						val = self.cv.null_create()
					print "External Call Result:", st, val
					return self.cv.COMARRetVal(st, val)
				break

	def runOMNode(self, prms = {}, Type = "", name = ""):
		print "OM NODE CALLED:", prms, Type , name
		prms = self._buildPrms(prms)		
		if Type == "method":
			return self.runenv.runMethod(name = name, prms = prms)
		elif Type == "propertyget":
			return self.runenv.runPropertyGet(name = name, prms = prms)
		elif Type == "propertyset":
			return self.runenv.runPropertySet(name = name, prms = prms )

	def	makeinstance(self, instid = ''):
		new = self.api.createNewInstance(instid, self.callerInfo)
		#self.api.saveValue(instid, self.instance, 'instance', new)
		#objType = "", instance = "", ci = None):
		for i in dir(new):
			print "\t", i, "=", getattr(new, i)
		#registerObject(self, objid  = "", objType="", callerInfo = None):
		rv = self.api.registerObject(objid = instid, objType = "CSL:OMINSTANCE",  callerInfo=new)
		self.procHelper.sendParentCommand(cmd = "TRSU_SOBJ", pid = self.procHelper.myPID, tid = 0, data=rv.object)
		return CSLValue('object', rv.object)

_HOOK			= COMARObjHook
