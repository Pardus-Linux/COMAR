#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2004, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.

# RPCData.py 
# COMAR-RPC Data Management Objects and Structures.


import time, xml.dom.minidom, copy, COMARValue, zlib, bz2, base64, cPickle

STATUS_CODES = ["ACCEPTED", "PROCESSED", "QUEUE", "WAIT", "RESULT", "PERMISSIONDENIED", "INVALID", "ABORT", "ERROR", "NOTFOUND", "FATAL", "KILLED", "ACCESSDENIED" ]

def	_debugout(stri):
	print "RPC Data Handler:", stri
class _PROPObject(object):
	def	__init__(self, rpc):
		self.rpcobj = rpc

	def	__getitem__(self, item):
		return self.rpcobj.getProperty(item)
	def	__setitem__(self, item, value):
		self.rpcobj.setProperty(item, value)
	def	__str__(self):
		return self.rpcobj.propertyList().__str__()

class RPCStruct(object):
	PriorityList = ["NORMAL", "URGENT", "INTERACTIVE", "DONTCARE"]
	def	__init__(self, TTSID="", EOL=0, Priority="NORMAL", xmlData = None):
		self.version	= "1.0"
		self._TTSID		= TTSID[:255]
		if EOL == 0:
			EOL = time.time() + 86400;
		self._EOL		= EOL
		self._RPCHandlers = {"RESPONSE":RPCResponse,
							 "OMCALL":	RPCOMCall,
							 "OBJCALL":	RPCObjCall,
							 "EXEC":	RPCExec,
							 "STATUS":	RPCStatus,
							 "NOTIFY":	RPCNotify,
							 "CANCEL":	RPCCancel}
		if Priority in self.PriorityList:
			self._priority	= Priority
		else:
			self._TTSID = ""
			return None
		self.data = None
		self._type = "NULL"
		if xmlData != None:
			x = self.load_value_xml(xmlString=xmlData)
			if x == 1:
				return None

	def	RPCModel(self):
		if self._type == "NOTIFY":
			return "notifier"
		elif self._type in ("CANCEL", "STATUS"):
			return "remote"
		elif self._type == "RESPONSE":
			return "local"
		else:
			return "new"

	def	toString(self):
		ser = "RPCDATA 1.0"+chr(0)
		ser += "TTSID=%s" % (self._TTSID) + chr(0)
		ser +=   "EOL=%s" % (self._EOL) + chr(0)
		ser +=  "PRIO=%s" % (self._priority) + chr(0)
		ser +=  "TYPE=%s" % (self._type) + chr(0)
		if self._type != "NULL":
			for p in self.data.propTable.keys():
				hnd = self.data.propTable[p]
				if (hnd[2] != None):
					vl = hnd[2](p,all=1)
					for v in vl.keys():
						#print "p=%s", v
						vd = cPickle.dumps(vl[v])
						ser += "p_%s[%s]=%s %s" % (p, v,  len(vd), vd) + chr(0)
				else:
					v = cPickle.dumps(self.getProperty(p))
					#print "Prop: %s=%d %s" % (p, len(v), v)
					ser += "v_%s=%d %s" % (p, len(v), v) + chr(0)

		return ser

	def	fromString(self, st = ""):
		if st[0:12] != "RPCDATA 1.0" + chr(0):
			print "Signature !"
			return 1
		st = st[st.find(chr(0))+1:]
		x = self._sprop(st, "TTSID", self.setTTSID)
		if x == -1:
			print "TTSID !:", st
			return 1
		st = st[x+1:]
		x = self._sprop(st, "EOL", self.setEOL)
		if x == -1:
			print "EOL !:", st
			return 1
		st = st[x+1:]
		x = self._sprop(st, "PRIO", self.setPriority)
		if x == -1:
			print "PRIO !:", st
			return 1
		st = st[x+1:]
		x = self._sprop(st, "TYPE", None)
		if x == -1:
			print "TYPE !:", st
			return 1

		st = st[x[0]+1:]
		#print "NEW TYPE:", x[1], st
		self.makeRPCData(x[1])

		while len(st)>1:

			e = st.find("=")
			ppos  = st.find(" ", e+1) + 1
			#print "e:", e,"st=", st[e+1:ppos]
			psize = int(st[e+1:ppos])
			p = st[:e]
			if psize:
				v = st[ppos:ppos+psize]
			else:
				v = ""
			#print "P:%s size:%d value: '%s'" % (p, psize, v)
			name = p[2:]
			if p[0] == "p":
				key = name[name.find("[")+1:len(name)-1]
				name = name[:name.find("[")]
				#print "MultiVal:", name, key
				self.addPropertyMulti(name, key, cPickle.loads(v))
			else:
				if psize:
					self.setProperty(name, cPickle.loads(v))

			st = st[st.find("\x00", ppos+psize)+1:]

	def _sprop(self, sta, cmp, call):
		x = sta.find(chr(0))
		if x == -1:
			return -1
		p = sta[:x]
		c = sta.find("=")
		if c == -1:
			return -1
		l = p[:c]
		v = p[c+1:]
		#print "_sprop: ", l, "V:", v[:30]
		if l == cmp:
			#print "_spropx: ", l, "V:", v[:30]
			if call:
				call(v)
			else:
				return (x,v)
			return x
		return -1

	def	pget(self):
		return _PROPObject(self)

	def	propertyList(self):
		if self.data:
			if self.data.propTable:
				return self.data.propTable.keys()
	def	propObject(self):
		return _PROPObject(self)

	def RPCHandlers(self):
		return self._RPCHandlers

	def addRPCHandler(self, HandlerID = "", Handler=None):
		if HandlerID == "" or Handler == None or self._type == HandlerID:
			return
		self._RPCHandlers[HandlerID] = Handler

	def	delRPCHandler(self, HandlerID = ""):
		if HandlerID == "" or self._type == HandlerID:
			del self._RPCHandlers[HandlerID]

	def	__getitem__(self, hnd = ""):
		if self.data:
			if self.data.propTable:
				if self.data.propTable[hnd]:
					if self.data.propTable[hnd][0]:
						return self.data.propTable[hnd][0]()
		return None
	def	__setitem__(self, hnd = "", value = None):
		if self.data:
			if self.data.propTable:
				if self.data.propTable[hnd]:
					if self.data.propTable[hnd][1]:
						return self.data.propTable[hnd][1](value)

	def	setProperty(self, propName = "", propValue = None):
		"""
			setProperty(propertyName, propertyValue)
		"""
		if self.data == None:
			return None
		if self.data.propTable.has_key(propName) == False:
			return None
		hnd = self.data.propTable[propName]
		if (hnd[1] != None):
			return hnd[1](propValue)
		return None

	def	addPropertyMulti(self, propName ="", propIndex = "", propValue = None):
		"""
			addPropertyMulti(propertyName, propertyIndex, propertyValue)
		"""
		if self.data == None:
			return None
		if self.data.propTable.has_key(propName) == False:
			return None
		hnd = self.data.propTable[propName]
		#print "ADDPM: ", hnd, hnd[3]
		if (hnd[3] != None):
			return hnd[3](propIndex, propValue)
		return None

	def	getPropertyMulti(self, propName ="", propIndex = "", all=0):
		"""
			getPropertyMulti(propertyName, propertyIndex)
		"""
		if all:
			return self.data.propTable[propName][2](all = 1)
		if self.data == None:
			return None
		if self.data.propTable.has_key(propName) == False:
			return None
		hnd = self.data.propTable[propName]
		if (hnd[2] != None):
			return hnd[2](propIndex)
		return None

	def	delPropertyMulti(self, propName ="", propIndex = ""):
		"""
			addPropertyMulti(propertyName, propertyIndex)
		"""
		if self.data == None:
			return None
		if self.data.propTable.has_key(propName) == False:
			return None
		hnd = self.data.propTable[propName]
		if (hnd[4] != None):
			return hnd[4](propIndex, propValue)
		return None

	def	getProperty(self, propName = ""):
		"""
			getProperty(propertyName)
		"""
		if self.data == None:
			return None
		if self.data.propTable.has_key(propName) == False:
			return None
		hnd = self.data.propTable[propName]
		if (hnd[0] != None):
			return hnd[0]()
		return None

	def	setXML(self, xml):
		pass
	def	getXML(self):
		return	self.dump_value_xml()

	def	setTTSID(self, value):
		self._TTSID		= value[:255]
	def getTTSID(self):
		return self._TTSID
	def	setEOL(self, value):
		try:
			self._EOL		= int(value);
		except:
			pass

	def	getEOL(self):
		return self._EOL
	def	getType(self):
		return self._type
	def	setPriority(self, Priority):
		if Priority in self.PriorityList:
			self._priority	= Priority
	def	getPriority(self):
		return self._priority
	def	setData(self,value):
		#print "set RPCData:", value
		if "RPCDataType" in dir(value):
			self.data	= value
			self._type	= value.RPCDataType
	def	getData(self):
		return self.data
	def	dump_value_xml(self, doc = None):
		""" Generic serialization function for RPCData """
		if self.data == None:
			return None

		if doc == None:
			dom = xml.dom.minidom.getDOMImplementation()
			doc = dom.createDocument(None, "COMARRPCData", None)
			root = doc.documentElement
		else:
			dom = None
			root = doc.createElement("COMARRPCData")

		root.appendChild(_setNode(doc, "RPCVersion", self.version))
		root.appendChild(_setNode(doc, "RPCTTSID", self._TTSID))
		root.appendChild(_setNode(doc, "RPCEOLTime", self._EOL.__str__()))
		root.appendChild(_setNode(doc, "RPCPriority", self._priority))
		root.appendChild(_setNode(doc, "RPCType", self._type))
		root.appendChild(self.data.toxmlNode(doc))
		if dom == None:
			return root
		txt = doc.toxml()
		doc.unlink()
		return txt
	def	load_value_xml(self, xmlString = "", doc = None, root = None):

		if doc == None:
			#print "Load XML Value:", xmlString
			doc = xml.dom.minidom.parseString(xmlString)
			#_debugout( "xml parsing successfull %s" % (doc))

		if doc == None:
			_debugout("XML Loader: Invalid XML Code or Internal Error: %s" % (xmlString))
			self._TTSID = ""
			return 1

		if root == None:
			root = doc.firstChild

		first = root.firstChild
		data = None
		self._TTSID = ""
		while first:
			if first.tagName == "RPCVersion":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				self.version = d
			if first.tagName == "RPCTTSID":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				self._TTSID = d
			if first.tagName == "RPCEOLTime":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				self._EOL = float(d)
			if first.tagName == "RPCPriority":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				if d in ["NORMAL", "URGENT", "INTERACTIVE", "DONTCARE"]:
					self._priority = d
				else:
					_debugout("XML Loader: Invalid Priority: %s" % (d))
					self._TTSID = ""
					return 1
			if first.tagName == "RPCType":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				self._type = d
				#print "Requested RPC Type:", d
			if first.tagName == "RPCData":
				data = first
			first = first.nextSibling
		# end of main loop

		if data != None:
			#print "Build RPC Data For Type:", self._type
			if self._type in self._RPCHandlers.keys():
				self.data = self._RPCHandlers[self._type](xmlData = data)
				#print "Builded RPC Data For Type:", self.data, self._type
			else:
				_debugout("XML Loader: Invalid Handler: %s" % (self._type))
				self._TTSID = ""
				return 1
		else:
			_debugout("XML Loader: RPCData Not found")
			self._TTSID = ""
			return 1

	def	isTimeout(self):
		if time.time() > self._EOL and self._EOL != 0:
			return 0
		return 1
	def	makeRPCData(self, RPCType = ""):
		if self._RPCHandlers.has_key(RPCType) == 0:
			return True
		self._type = RPCType
		self.data  = self._RPCHandlers[RPCType]()

	TTSID		= property(getTTSID, setTTSID, None, "TTSID")
	EOLTime		= property(getEOL, setEOL, None, "End-of-life. Epoch Time")
	Type 		= property(getType, None, None, "RPC Type. Valid values as RESPONSE, OMCALL, OBJCALL, EXEC, STATUS, NOTIFY, CANCEL\nDo not set directly, If you set RPCData property, this property uses RPCDataType")
	Priority 	= property(getPriority, setPriority, None, "Priority: Valid values as: NORMAL, URGENT, INTERACTIVE, DONTCARE")
	RPCPriority 	= property(getPriority, setPriority, None, "Priority: Valid values as: NORMAL, URGENT, INTERACTIVE, DONTCARE")
	RPCData		= property(getData, setData, None, "RPCData Object for this call")
	xml			= property(getXML, setXML, None, "XML Representation of Object. If set, all object data restored from xml string")

class	RPCOMCall:
	def	__init__(self, Type = "propertyget", name = "_default", index = "", xmlData=None):
		self.propTable = { "type":		(self.TypeIO, self.TypeIO, None, None, False),
						   "name":		(self.NameIO, self.NameIO, None, None, False),
						   "index":		(self.IndexIO, self.IndexIO, None, None, False),
						   "parameter":	(None, None, self.getParameter, self.addParameter, self.delParameter) }
		if xmlData != None:
			self.RPCDataType = "OMCALL"
			self.name = ""
			self.index = ""
			self.prms = {}
			x = self.initFromXml(xmlNode = xmlData)
			if x != None:
				return None
		else:
			if Type in ["propertyget", "propertyset", "method"]:
				self.type = Type[:255]
			else:
				return None
			self.RPCDataType = "OMCALL"
			self.name	= name[:255]
			self.index	= index[:255]
			self.prms	= {}
	def	TypeIO(self,  value=None):
		if value != None:
			if value in ["propertyget", "propertyset", "method"]:
				self.type = value[:255]
		else:
			return self.type
	def	NameIO(self, value=None):
		if value != None:
			self.name = value[:255]
		else:
			return self.name
	def	IndexIO(self, value=None):
		if value != None:
			self.index = value[:255]
		else:
			return self.index

	def	delParameter(self, prmName=""):
		if prmName=="":
			return None
		if self.prms.has_key(prmName):
			del self.prms[prmName]

	def	addParameter(self, name="", value=None):
		if name=="":
			return None
		if "type" in dir(value):
			#if self.type == "method":
			self.prms[name] = value
			#else:
			#	self.prms[0] = value

	def	getParameters(self):
		return copy.deepcopy(self.prms)

	def	getParameter(self, prm = "",all=0):
		if all:
			ret = {}
			for p in self.prms.keys():
				ret[p] = self.prms[p]
			return ret

		if self.prms.has_key(prm):
			return self.prms[prm]
		return None

	def	initFromXml(self, xmlNode = None):
		if xmlNode == None:
			return None
		first = xmlNode.firstChild
		while first:
			if first.tagName == "type":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				if d in ["propertyget", "propertyset", "method"]:
					self.type = d
				else:
					return 1
			elif first.tagName == "name":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				self.name = d[:255]
			elif first.tagName == "index":
				d = ""
				if first.firstChild:
					d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				self.index = d
			elif first.tagName == "parameters":
				# Difficult point..
				node = first.firstChild
				while node:
					if node.tagName == "parameter":
						chld = node.firstChild
						prmname = None
						value = None
						while chld:
							if chld.tagName == "name":
								d = chld.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
								prmname = d
							elif chld.tagName == "value":
								value = COMARValue._load_value_xml(chld.firstChild)
							chld=chld.nextSibling
						if prmname != None and value != None:
							self.prms[prmname] = value
					node = node.nextSibling
			first = first.nextSibling

	def	toxmlNode(self, doc):
		node = doc.createElement("RPCData")
		node.appendChild(_setNode(doc, "type", self.type))
		node.appendChild(_setNode(doc, "name", self.name))
		node.appendChild(_setNode(doc, "index", self.index))
		prms = doc.createElement("parameters")
		k = self.prms.keys()
		for i in k:
			#print "KEY: ", i, "Value:", self.prms[i]
			tnode = doc.createElement("parameter")
			tnode.appendChild(_setNode(doc, "name", i.__str__()))
			vnode = doc.createElement("value")
			COMARValue._dump_value_xml(self.prms[i], doc, vnode)
			tnode.appendChild(vnode)
			prms.appendChild(tnode)
		node.appendChild(prms)
		return node

class	RPCObjCall:
	def	__init__(self, obj = None, Type = "propertyget", name = "_default", index = "", xmlData = None):
		self.propTable = { "name":		(self.NameIO, 			self.NameIO,	None, None, None),
						   "type":		(self.TypeIO, 			self.TypeIO,	None, None, None),
						   "index":		(self.IndexIO, 			self.IndexIO,	None, None, None),
						   "object":	(self.ObjectIO, 		self.ObjectIO,	None, None, None),
						   "parameter":	(None, None, self.getParameter, self.addParameter, self.delParameter) }
		if xmlData != None:
			self.RPCDataType = "OBJCALL"
			self.name	= ""
			self.index	= ""
			self.object = None
			self.prms	= {}
			x = self.initFromXml(xmlData)
			if x != None:
				return None
		else:
			if Type in ["propertyget", "propertyset", "method"]:
				self.type = Type[:255]
			else:
				return None
			self.RPCDataType = "OBJCALL"
			self.name	= name[:255]
			self.index	= index[:255]
			self.object = obj
			self.prms	= {}
	def	TypeIO(self, value=None):
		if value != None:
			if Type in ["propertyget", "propertyset", "method"]:
				self.type = Type[:255]
			else:
				return None
		else:
			return self.type
	def	ObjectIO(self, value=None):
		if value != None:
			self.object = value
		else:
			return self.object

	def	NameIO(self, value=None):
		if value != None:
			self.name = value[:255]
		else:
			return self.name

	def	IndexIO(self, value=None):
		if value != None:
			self.index = value[:255]
		else:
			return self.index

	def	addParameter(self, name="", value=None):
		if name=="":
			return None
		if "type" in dir(value):
			if self.type == "method":
				self.prms[name] = value
			else:
				self.prms[0] = value

	def	delParameter(self, name=""):
		if name=="":
			return None
		if self.prms.has_key(name):
			del self.prms[name]

	def	getParameters(self):
		return copy.deepcopy(self.prms)

	def	getParameter(self, name = "", all = 0):
		if all:
			ret = {}
			for p in self.prms.keys():
				ret[p] = self.prms[p]
			return ret
		prm = name
		if self.prms.has_key(prm):
			return self.prms[prm]
		return None

	def	initFromXml(self, xmlNode = None):
		if xmlNode == None:
			return None
		first = xmlNode.firstChild
		while first:
			if first.tagName == "type":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				if d in ["propertyget", "propertyset", "method"]:
					self.type = d
				else:
					return 1
			elif first.tagName == "name":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				self.name = d[:255]
			elif first.tagName == "index":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				self.index = d
			elif first.tagName == "object":
				self.obj = COMARValue._load_value_xml(first)
			elif first.tagName == "parameters":
				# Difficult point..
				node = first.firstChild
				while node:
					if node.tagName == "parameter":
						chld = node.firstChild
						prmname = None
						value = None
						while chld:
							if chld.tagName == "name":
								d = chld.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
								prmname = d
							elif chld.tagName == "value":
								value = COMARValue._load_value_xml(chld.firstChild)
							chld=chld.nextSibling
						if prmname != None and value != None:
							self.prms[prmname] = value
					node = node.nextSibling
			first = first.nextSibling
	def	toxmlNode(self, doc):
		node = doc.createElement("RPCData")
		node.appendChild(_setNode(doc, "type", self.type))
		node.appendChild(_setNode(doc, "name", self.name))
		node.appendChild(_setNode(doc, "index", self.index))
		COMARValue._dump_value_xml(self.object, doc, node)
		prms = doc.createElement("parameters")
		k = self.prms.keys()
		for i in k:
			#print "KEY: ", i, "Value:", self.prms[i]
			tnode = doc.createElement("parameter")
			tnode.appendChild(_setNode(doc, "name", i.__str__()))
			vnode = doc.createElement("value")
			COMARValue._dump_value_xml(self.prms[i], doc, vnode)
			tnode.appendChild(vnode)
			prms.appendChild(tnode)
		node.appendChild(prms)
		return node

class	RPCExec(object):
	def	__init__(self, code = "", compress="NONE", Type = "propertyget", name = "_default", index = "", xmlData=None):
		self.propTable = { "name":			(self.NameIO, 			self.NameIO,	None, None, None),
						   "compression":	(self.getCompress, 		self.setCompress,	None, None, None),
						   "index":			(self.IndexIO, 			self.IndexIO,	None, None, None),
						   "type":			(self.TypeIO, 			self.TypeIO,	None, None, None),
						   "code":			(self.getCode, 			self.setCode,	None, None, None),
						   "parameter":		(None, None, self.getParameter, self.addParameter, self.delParameter) }
		self.RPCDataType = "EXEC"
		self.name	= ""
		self.index	= ""
		self.code = ""
		self._compress = ""
		self.prms	= {}
		if xmlData != None:
			x = self.initFromXml(xmlData)
			if x != None:
				return None
		else:
			if not compress in ["GZIP", "BZIP2", "NONE"]:
				print "Invalid Compression:", compress
				return None

			if Type in ["propertyget", "propertyset", "method"]:
				self.type = Type[:255]
			else:
				return None


			self._compress = compress
			self.setCode(code)
			self.name	= name[:255]
			self.index	= index[:255]

		print self._compress
	def	TypeIO(self, value=None):
		if value != None:
			if Type in ["propertyget", "propertyset", "method"]:
				self.type = Type[:255]
			else:
				return None
		else:
			return self.type
	def	NameIO(self, value=None):
		if value != None:
			self.name = value[:255]
		else:
			return self.name

	def	IndexIO(self, value=None):
		if value != None:
			self.index = value[:255]
		else:
			return self.index

	def	addParameter(self, prmName="", value=None):
		if prmName=="":
			return None
		if "type" in dir(value):
			if self.type == "method":
				self.prms[prmName] = value
			else:
				self.prms[0] = value
	def	getParameters(self):
		return copy.deepcopy(self.prms)

	def	delParameter(self, prmName=""):
		if prmName=="":
			return None
		if self.prms.has_key(prm):
			del self.prms[prm]

	def	getParameter(self, prm = "", all = 0):
		if all:
			ret = {}
			for p in self.prms.keys():
				ret[p] = self.prms[p]
			return ret
		if self.prms.has_key(prm):
			return self.prms[prm]
		return None
	def	getCompress(self):
		return self._compress
	def	setCompress(self, compress):
		if not compress in ["NONE", "GZIP", "BZIP2"]:
			return
		if self._compress != "NONE":
			self.code = base64.decodestring(self.code)
		if compress != self._compress:
			if self._compress == "GZIP":
				if len(self.code): self.code = zlib.decompress(self.code)
			elif self._compress == "BZIP2":
				if len(self.code): self.code = bz2.decompress(self.code)
			if compress == "GZIP":
				if len(self.code): self.code = zlib.compress(self.code)
			elif compress == "BZIP2":
				if len(self.code): self.code = bz2.compress(self.code)
			self._compress = compress
			if compress != "NONE":
				if len(self.code): self.code = base64.encodestring(self.code)

	def setCode(self, code):
		#print self._compress
		if self._compress == "GZIP":
			code = zlib.compress(code)
		elif self._compress == "BZIP2":
			code = bz2.compress(code)
		if self._compress != "NONE":
			code = base64.encodestring(code)

		self.code = code
	def getCode(self):
		if self._compress != "NONE" and self._compress != "":
			if len(self.code):
				cstr = base64.decodestring(self.code)
		else:
			cstr = self.code

		if self._compress == "GZIP":
			if len(self.code):
				cstr = zlib.decompress(cstr)
		elif self._compress == "BZIP2":
			if len(self.code):
				cstr = bz2.decompress(cstr)

		return cstr
	def	initFromXml(self, xmlNode = None):
		if xmlNode == None:
			return None
		first = xmlNode.firstChild
		while first:
			if first.tagName == "type":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				if d in ["propertyget", "propertyset", "method"]:
					self.type = d
				else:
					return 1
			elif first.tagName == "name":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				self.name = d[:255]
			elif first.tagName == "index":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				self.index = d[:255]
			elif first.tagName == "code":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				self.code = d[:65535]
			elif first.tagName == "compression":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				self._compress = d
			elif first.tagName == "parameters":
				# Difficult point..
				node = first.firstChild
				while node:
					if node.tagName == "parameter":
						chld = node.firstChild
						prmname = None
						value = None
						while chld:
							if chld.tagName == "name":
								d = chld.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
								prmname = d
							elif chld.tagName == "value":
								value = COMARValue._load_value_xml(chld.firstChild)
							chld=chld.nextSibling
						if prmname != None and value != None:
							self.prms[prmname] = value
					node = node.nextSibling
			first = first.nextSibling
		if self._compress == "GZIP":
			self.code = base64.decodestring(self.code)
			self.code = zlib.decompress(self.code)
		elif self._compress == "BZIP2":
			self.code = base64.decodestring(self.code)
			self.code = bz2.decompress(self.code)
		elif self._compress != "NONE":
			return 1

	def	toxmlNode(self, doc):
		node = doc.createElement("RPCData")
		node.appendChild(_setNode(doc, "type", self.type))
		node.appendChild(_setNode(doc, "name", self.name))
		node.appendChild(_setNode(doc, "index", self.index))
		node.appendChild(_setNode(doc, "compression", self._compress))
		node.appendChild(_setNode(doc, "code", self.code))
		prms = doc.createElement("parameters")
		k = self.prms.keys()
		for i in k:
			#print "KEY: ", i, "Value:", self.prms[i]
			tnode = doc.createElement("parameter")
			tnode.appendChild(_setNode(doc, "name", i.__str__()))
			vnode = doc.createElement("value")
			COMARValue._dump_value_xml(self.prms[i], doc, vnode)
			tnode.appendChild(vnode)
			prms.appendChild(tnode)
		node.appendChild(prms)
		return node
	Code		= property(getCode, setCode, None, "Code for execute remote call")
	Compression	= property(getCompress, setCompress, None, "Compression method for transmission")

class	RPCResponse:
	def	__init__(self, TTSID = "", status = "", retval = None, xmlData = None):
		self.propTable = { "TTSID":		(self.ttsIO, 			self.ttsIO,	None, None, None),
						   "status":	(self.getStatus, 		self.setStatus,	None, None, None),
						   "returnvalue":(self.getRetVal, 		self.setRetVal,	None, None, None) }
		self._TTSID = TTSID
		if xmlData != None:
			self.RPCDataType = "RESPONSE"
			self.status = ""
			self.retval = None
			self._TTSID = ""
			x = self.initFromXml(xmlData)
			if x != None:
				return None
		else:
			if status in STATUS_CODES:
				self.status = status
			else:
				return None
			self.retval = None
			self._TTSID = TTSID
			if status == "RESULT":
				self.retval = retval


	def	ttsIO(self, value=None):
		if value != None:
			self._TTSID = value
		else:
			return self._TTSID

	def setRetVal(self, ret):
		if self.status != "RESULT":
			return
		self.retval = ret
	def getRetVal(self):
		return self.retval

	def	getStatus(self):
		return self.status
	def	setStatus(self, stat):
		if stat in STATUS_CODES:
			self.status = stat
			if stat != "RESULT":
				self.retval = None

	def	initFromXml(self, xmlNode = None):
		if xmlNode == None:
			return None
		first = xmlNode.firstChild
		rval	= None
		res		= None
		while first:
			if first.tagName == "TTSID":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				self.TTSID = d[:255]
			elif first.tagName == "status":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				if d in STATUS_CODES:
					self.status = d
				else:
					return 1
			elif first.tagName == "retval":
				rvnode = first.firstChild
				while rvnode:
					if rvnode.tagName == "execresult":
						res = rvnode.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
					elif rvnode.tagName == "returnvalue":
						tmp = rvnode.firstChild
						rval = COMARValue._load_value_xml(tmp)
					rvnode = rvnode.nextSibling
			first = first.nextSibling
		if rval != None and res != None:
			if self.status == "RESULT":
				self.retval = COMARValue.COMARRetVal(result = int(res), value = rval)

	def	toxmlNode(self, doc):
		node = doc.createElement("RPCData")
		node.appendChild(_setNode(doc, "TTSID", self.TTSID))
		node.appendChild(_setNode(doc, "status", self.status))
		if self.retval != None:
			rv = doc.createElement("retval")
			rv.appendChild(_setNode(doc, "execresult", self.retval.execResult.__str__()))
			tmp = doc.createElement("returnvalue")
			COMARValue._dump_value_xml(self.retval.returnValue, doc, tmp)
			rv.appendChild(tmp)
			node.appendChild(rv)
		return node

	Returnvalue		= property(getRetVal, setRetVal, None, "Return value")
	Status			= property(getStatus, setStatus, None, "Status constant")
	TTSID			= property(ttsIO, ttsIO, None, "Status constant")

class	RPCStatus:
	def	__init__(self, TTSID = "", stat = "", xmlData = None):
		self.propTable = { "TTSID":		(self.ttsIO, 			self.ttsIO,	None, None, None),
						   "status":	(self.statusIO, 		self.statusIO,	None, None, None) }
		self.RPCDataType = "STATUS"
		self.status = ""
		self.TTSID = ""
		if xmlData != None:
			x = self.initFromXml(xmlData)
			if x != None:
				return None
		else:
			if stat in STATUS_CODES:
				self.RPCDataType = "STATUS"
				self.status = stat
				self.TTSID = TTSID
			else:
				return None

	def	ttsIO(self, value=None):
		if value != None:
			self.TTSID = value
		else:
			return self.TTSID

	def	statusIO(self, value=None):
		if value != None:
			if value in STATUS_CODES:
				self.status = value
		else:
			return self.status

	def	initFromXml(self, xmlNode = None):
		if xmlNode == None:
			return None
		first = xmlNode.firstChild
		while first:
			if first.tagName == "TTSID":
				if first.firstChild != None:
					d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
					self.TTSID = d[:255]
			#elif first.tagName == "status":
			#	if first.firstChild != None:
			#		d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
			#		if d in STATUS_CODES:
			#			self.status = d
			#		else:
			#			return 1
			first = first.nextSibling

	def	toxmlNode(self, doc):
		node = doc.createElement("RPCData")
		node.appendChild(_setNode(doc, "TTSID", self.TTSID))
		#node.appendChild(_setNode(doc, "status", self.status))
		return node

class	RPCNotify:
	def	__init__(self, eventid = "", stat = "", xmlData = None):
		self.propTable = { "eventid":	(self.eventIO, 	self.eventIO,	None, None, None),
						   "status":	(self.statusIO,	self.statusIO,	None, None, None) }
		if xmlData != None:
			self.RPCDataType = "NOTIFY"
			self.status = ""
			self.eventid = ""
			x = self.initFromXml(xmlData)
			if x != None:
				return None
		else:
			if stat in STATUS_CODES:
				self.status = stat
				self.eventid = eventid
			else:
				return None


	def	eventIO(self, value=None):
		if value != None:
			self.eventid = value
		else:
			return self.eventid

	def	statusIO(self, value=None):
		if value != None:
			if value in STATUS_CODES:
				self.status = value
		else:
			return self.status

	def	initFromXml(self, xmlNode = None):
		if xmlNode == None:
			return None
		first = xmlNode.firstChild
		while first:
			if first.tagName == "eventid":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				self.eventid = d[:255]
			elif first.tagName == "status":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				if d in STATUS_CODES:
					self.status = d
				else:
					return 1
			first = first.nextSibling

	def	toxmlNode(self, doc):
		node = doc.createElement("RPCData")
		node.appendChild(_setNode(doc, "status", self.status))
		node.appendChild(_setNode(doc, "eventid", self.eventid))
		return node

class	RPCCancel:
	def	__init__(self, TTSID = ""):
		self.RPCDataType = "CANCEL"
		self.TTSID = TTSID
		self.propTable = { "TTSID":	(self.eventIO, 	self.eventIO,	None, None, None) }

	def	eventIO(self, value=None):
		if value != None:
			self.TTSID = value
		else:
			return self.TTSID

	def	toxmlNode(self, doc):
		node = doc.createElement("RPCData")
		node.appendChild(_setNode(doc, "TTSID", self.TTSID))
		return node

	def	initFromXml(self, xmlNode = None):
		if xmlNode == None:
			return None
		first = xmlNode.firstChild
		while first:
			if first.tagName == "TTSID":
				d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
				self.TTSID = d[:255]
			first = first.nextSibling

def	_setNode(doc, tag, value):
		node = doc.createElement(tag)
		txtNode = doc.createTextNode(value)
		node.appendChild(txtNode)
		return node

class	userInfo:
	def	__init__(self, str = ""):
		self.name	= ""
		self.realm	= ""
		self.group	= ""
		self.uid	= 500
		if str != "":
			self.fromString(str)

	def	toString(self):
		ser = "USERDATA 1.0"+chr(0)
		return ser + cPickle.dumps(self)
		return ser

	def	fromString(self, st = ""):
		if st[0:13] != "USERDATA 1.0" + chr(0):
			print "Signature !"
			return 1
		st = st[st.find(chr(0))+1:]
		s = cPickle.loads(st)
		self.name = s.name
		self.realm = s.realm
		self.group = s.group
		self.uid = s.uid

	def	toXml(self, doc=None):
		if doc == None:
			dom = xml.dom.minidom.getDOMImplementation()
			doc = dom.createDocument(None, "userinfo", None)
			root = doc.documentElement
		else:
			dom = None
			root = doc.createElement("userinfo")
		node = root
		node.appendChild(_setNode(doc, "name", self.name))
		node.appendChild(_setNode(doc, "group", self.group))
		node.appendChild(_setNode(doc, "realm", self.realm))
		if dom:
			x = doc.toxml()
			doc.unlink()
			return x
		else:
			return node
	def	fromXml(self, xmlString = "", doc = None, root = None):
		if doc == None:
			#print "Load XML Value:", xmlString
			doc = xml.dom.minidom.parseString(xmlString)
			#_debugout( "xml parsing successfull %s" % (doc))
		if doc == None:
			_debugout("XML Loader: Invalid XML Code or Internal Error: %s" % (xmlString))
			self._TTSID = ""
			return 1
		if root == None:
			root = doc.firstChild

		first = root.firstChild
		data = None
		while first:
			if first.tagName == "name":
				if first.firstChild:
					d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
					self.name = d
			if first.tagName == "realm":
				if first.firstChild:
					d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
					self.realm = d
			if first.tagName == "group":
				if first.firstChild:
					d = first.firstChild.data[:].encode(COMARValue.GLO_ENCODING)
					self.group = d
			first = first.nextSibling

	def _sprop(self, sta, cmp, call):
		x = sta.find(chr(0))
		if x == -1:
			return -1
		p = sta[:x]
		c = sta.find("=")
		if c == -1:
			return -1
		l = p[:c]
		v = p[c+1:]
		#print "_sprop: ", l, "V:", v[:30]
		if l == cmp:
			#print "_spropx: ", l, "V:", v[:30]
			return (x,v)
		return -1
class	connectionInfo:
	def	__init__(self, str = ""):
		self.protocol	= ""
		self.protoAddr	= ""	# Opaque Data for connector.
		self.host		= ""	# Host part (fqdn) of connection..
		self.auth		= 0		# Authenticated ?
		self.secure		= 0		# Secure/Plain(0)
		self.verified	= 0		# Verified? PGP etc.
		self.isStream	= 0		# Stream(1)/Datagram(0)
		self.online		= 0		# online currently ? Changed with INTU_OFF
		self.TID		= 0		# TID Value. Used for Connection provider.
		self.CID 		= 0

		if str != "":
			self.fromString(str)
	def	toString(self):
		ser = "CONNINFO 1.0"+chr(0) + cPickle.dumps(self)
		return ser
	def	fromString(self, st = ""):
		if st[0:13] != "CONNINFO 1.0" + chr(0):
			print "Signature !"
			return 1
		st = st[st.find(chr(0))+1:]
		s = cPickle.loads(st)
		self.protocol	= s.protocol
		self.protoAddr	= s.protoAddr
		self.auth		= s.auth
		self.secure		= s.secure
		self.verified	= s.verified
		self.isStream	= s.isStream
		self.online		= s.online
		self.TID		= s.TID
		self.CID		= s.CID
