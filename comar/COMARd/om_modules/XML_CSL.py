#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2004, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

# XML_CSL.py
# COMAR OM module for xml based system models

# python modules
import bsddb
import xml.dom
import xml.dom.minidom
import codecs, md5
import os, dircache, sys, gzip
from errno import *

# comar modules
import comar_global
import ACL

NODE_UNKNOWN = 0
NODE_OBJECT = 1
NODE_METHOD = 2
NODE_PROPERTY = 3

class NodeData:
	def __init__(self, str=None):
		self.type = NODE_UNKNOWN
		self.index = -1
		if str != None:
			a = str.split()
			self.type = int(a[0])
			self.index = int(a[1])

	def toString(self):
		a = str(self.type) + " " + str(self.index)
		return a

class Obj:
	def __init__(self, str=None):
		self.IID = ""
		self.type = ""
		self.code_index = ""
		self.fname = ""
		if str != None:
			a = str.split("\t", 3)
			self.IID = a[0]
			self.type = a[1]
			self.code_index = a[2]
			self.fname = a[3]

	def toString(self):
		a = self.type + "\t" + self.IID + "\t" + self.code_index + "\t" + self.fname
		return a

class ObjList:
	def __init__(self, stri=None):
		self.pre = []
		self.hook = []
		self.post = []		
		if stri != None:			
			stri = str(stri)
			a = stri.split("\n")
			b = a[0].split("\t")
			print "OBJSTRING:", a, b
			print "PRE:", b
			for c in b:
				if c != "":
					self.pre.append(c)
			b = a[1].split("\t")
			print "HOOK:", b
			for c in b:			
				if c != "":
					self.hook.append(c)
			b = a[2].split("\t")
			print "POST:", b
			for c in b:
				if c != "":
					self.post.append(c)

	def toString(self):
		a = ""
		for o in self.pre:
			a += o + "\t"
		a = a[:-1]
		a += "\n"
		
		for o in self.hook:
			a += o + "\t"
		if a[-1] == "\t":
			a = a[:-1]
		a += "\n"
		for o in self.post:
			a += o + "\t"
		if a[-1] == "\t":
			a = a[:-1]
		return a

class OM_XML_CSL:
	def __init__(self, callInfo = None, objAPI = None, useNS = "", defFile = "", mainOMGR = None):
		self.main	= mainOMGR
		self.callInfo = callInfo
		self.obj_api = objAPI
		self.useNS   = useNS
		self.defFile = defFile
		self.dbhelper = None
		self.SrcStock = comar_global.comar_om_src
		#
		self.om_db_max = 0
		self.om_db = -1
		self.obj_db = -1
		self.app_db = -1
		self.scripts_db = -1
		self.acl_db = -1
		self.iid_db = -1
		self.inx_db = -1
		#

	def convert (self, text):
		a = codecs.getdecoder ("ascii")
		b = codecs.getencoder ("utf-8")
		tmp = a (text)
		return b (tmp[0]) [0]

	def make_name(self,node):
		name = None
		while node != None:
			if name == None:
				name = node.getAttribute("name")
			else:
				name = node.getAttribute("name") + "." + name
			node = node.parentNode
			if node.localName == "namespace":
				return name
		return name

	def load_node(self,node):
		types = { "object": NODE_OBJECT, "method": NODE_METHOD, "property": NODE_PROPERTY }
		if node.nodeType != xml.dom.Node.ELEMENT_NODE:
			return
		if types.has_key(node.localName):
			# FIXME: aptal python unicode key kabul etmem diyor
			key = self.convert(self.make_name(node))
			a = NodeData()
			a.type = types[node.localName]
			
			a.index = self.om_db_max
			self.om_db_max += 1
			self.dbhelper.dbWrite(self.om_db, key, a.toString())
			# set default acl
			acl = ACL.ACL()
			acl.fromXML(node)
			at = acl.toString()
			if at == None:
				at = ""
			self.dbhelper.dbWrite(self.acl_db, str(a.index), at)
			# recurse to children
			if a.type == NODE_OBJECT:
				for child in node.childNodes:
					self.load_node(child)
			print "%s(%s) " % (key, a.type),
			
	
	def load(self):
		d1 = self.dbhelper.dbRead(self.om_db, "xml_date")
		d2 = os.stat(self.defFile).st_mtime
		print "XML_CSL_LOAD", d1, d2
		if d1 != None:
			if d1 > d2:
				# FIXME: hata vermek yerine db'leri sifirlayip yeniden olustur
				print "XML_CSL: OOPS, xml om definition is newer than om db"
				print "XML_CSL: please remove db files manually"
				return
			else:
				return
		print "XML_CSL: creating om DBs..."
		try:
			dom = xml.dom.minidom.parse(self.defFile)
		except:
			print "OMDB: cannot parse '%s'" % (self.defFile)
			return 0
		if dom.documentElement.localName != "comar-om":
			print "OMDB: '%s' is not a COMAR om dtd" % (self.defFile)
			return 0
		ns = dom.getElementsByTagName("namespace")[0]
		# FIXME: namespace in useNS ile ayni oldugunu dogrula
		self.namespace = ns.getAttribute("name")
		print "Adding OM Keys:",
		for node in ns.childNodes:
			self.load_node(node)
			
		dom.unlink()
		if d1 == None:
			self.dbhelper.dbWrite(self.om_db, "xml_date", str(d2))
		return 1

	def setDBHelper(self, helper):
		self.dbhelper = helper		
		print "CSL_XML DB Initialization:", helper
		self.om_db = helper.dbOpen(comar_global.comar_om_db + "/" + self.useNS + "-om.db")
		self.obj_db = helper.dbOpen(comar_global.comar_om_db + "/" + self.useNS + "-obj.db")
		self.scripts_db = helper.dbOpen(comar_global.comar_om_db + "/" + self.useNS + "-scripts.db")
		self.acl_db = helper.dbOpen(comar_global.comar_om_db + "/" + self.useNS + "-acl.db")
		self.iid_db = helper.dbOpen(comar_global.comar_om_db + "/" + self.useNS + "-iids.db")
		self.inx_db = helper.dbOpen(comar_global.comar_om_db + "/" + self.useNS + "-inx.db")
		print "XML_CSL_OM: dbset:", self.om_db, self.obj_db, self.scripts_db, self.acl_db, self.iid_db, self.inx_db

	def postInit(self):
		# postInit called after setting dbhelper
		self.load()

	def destroy(self):
		pass

	def getCINFO(self, nodeKey):
		ci = self.callInfo()	
		omkey = nodeKey[:]		
		nodeKey = nodeKey[nodeKey.find(":") + 1:]
		IID = self.dbhelper.dbRead(self.iid_db, nodeKey + "_iid")
		node = self.dbhelper.dbRead(self.iid_db, nodeKey + "_node")
		fname = self.dbhelper.dbRead(self.iid_db, nodeKey + "_fname")
		print "IID DB RECS:", nodeKey, IID, node, fname
		if not (None in [ IID, node, fname ]):				
			ci.IID = IID
			ci.OID = "COMAR:" + node + "." + IID + "." + nodeKey
			ci.mode = "auto"
			ci.omkey = omkey
			return (self.obj_api, ci)
			
	def addNewInstance(self, node = "", index = "", key = "", instanceid = ""):
		rv = self.obj_api.COMARValue.null_create()		
		a = self.dbhelper.dbRead(self.inx_db, node)
		
		if not a:
			a = ""
			
		if a.find(index + "\x00") == -1:
			a = a + index + "\x00"
			self.dbhelper.dbWrite(self.inx_db, key, a)
		else:
			return self.obj_api.COMARValue.COMARRetVal(EEXIST, rv)
		inx = node + "_" + inx
		self.dbhelper.dbWrite(self.inx_db, inx, key + ":" + instanceid)
		return self.obj_api.COMARValue.COMARRetVal(0, rv)
		
	def addNodeScript(self, node = "", IID = "", code = "", fileName="", scriptType="CSL"):
		# check that node really exists and is an object
		
		a = self.dbhelper.dbRead(self.om_db, node)
		rv = self.obj_api.COMARValue.null_create()
		if not a:
			print "XML_CSL OM AddScript: Invalid Node Key:", node, "->", a
			return self.obj_api.COMARValue.COMARRetVal(EINVAL, rv)
		nd = NodeData(a)
		if nd.type != NODE_OBJECT:
			print "XML_CSL OM AddScript: Invalid Node Object:", a, nd
			return self.obj_api.COMARValue.COMARRetVal(EINVAL, rv)
		# get registered obj list
		a = self.dbhelper.dbRead(self.obj_db, str(nd.index))
		print "XML_CSL_OM: Registered Object:", a
		if a:		
			objs = ObjList(a)
		else:
			objs = ObjList()
		# append code to script db
		m = md5.new(IID + fileName)
		id = m.hexdigest()
		ci = self.callInfo()
		ci.IID = IID
		ci.OID = "COMAR:" + node + "." + IID + "." + id
		ci.mode = "load"
		self.dbhelper.dbWrite(self.iid_db, id+"_node", node)
		self.dbhelper.dbWrite(self.iid_db, id+"_iid", IID)
		self.dbhelper.dbWrite(self.iid_db, id+"_fname", fileName)
		
		ipt = self.main.getObjHook(scriptType)
		print "IPT=", ipt, ci.OID
		gcc = ipt(cAPI = self.obj_api, callerInfo = ci, chldHelper = self.dbhelper)
		gcc.loadInstance(instanceid = id)
		#gcc = self.objhooks[scriptType](instanceid = id, cAPI = self.objAPI, callerInfo = ci, chldHelper = self.dbhelper)
		objCode = gcc.compile(code)
		objCode = gzip.zlib.compress(objCode)
		self.dbhelper.dbWrite(self.scripts_db, id,  objCode)
		# FIXME: script id yi app db ye de yaz
		gcc.setSourceFromDBKey(comar_global.comar_om_db + "/%s-scripts.db" % (self.useNS), id)
		# append new object
		# FIXME: check for duplicates
		obj = Obj()
		obj.IID = IID
		obj.fileName = fileName
		obj.type = scriptType
		obj.code_index = id
		objs.hook.append(obj.type + ":" + obj.code_index)
		self.dbhelper.dbWrite(self.obj_db, str(nd.index), objs.toString())
		#print "OBJ_API Dir:", dir(self.obj_api)		
		return self.obj_api.COMARValue.COMARRetVal(0, rv)
		
	def getOMObjList(self, node = ""):
		# find node index
		a = self.dbhelper.dbRead(self.om_db, node)
		if not a:
			return None
		nd = NodeData(a)
		if nd.type in [ NODE_METHOD, NODE_PROPERTY ]:
			obname = node[:node.rfind(".")]
			while 1:
				a = self.dbhelper.dbRead(self.om_db, obname)
				if a:
					nd = NodeData(a)
					if nd.type == NODE_OBJECT:
						print "Found Object:", obname, nd.index
						break
				x = obname.rfind(".")
				if x == -1:
					return None
				obname = obname[:x]
				
		# get registered obj list
		a = self.dbhelper.dbRead(self.obj_db, str(nd.index))
		print "KEY STRING:", nd.index, "=", a
		objs = ObjList(a)
		# return keys
		keys = []
		print "OBJS.HOOK:", objs.hook
		for o in objs.hook:
			print "o:", o
			key = o # str(nd.index) + ":" +
			keys.append(key)
		return keys

	def getOMObj(self, key = ""):
		a = key.split(":")
		print "\n\nGetOMObj Key:", key, a
		hook = self.main.getObjHook(a[0])
		return (hook, None, a[1])

	def getOMProperties(self, key = ""):
		a = self.dbhelper.dbRead(self.om_db, key)
		print "A 'a' =", a
		if a != None and len(str(a)) > 0:
			return ( "usecontainer", "multicall" )

	def checkACL(self, node, userInfo, connInfo):
		# check node
		t = self.dbhelper.dbRead(self.om_db, node)
		if not t:
			# no such node, deny
			return 0
		nd = NodeData(t)
		# check acls
		acl = ACL.ACL()
		t = self.dbhelper.dbRead(self.acl_db, nd.index)
		if not t:
			# no acl defined, deny by default
			return 0
		acl.fromString(t)
		if acl.standalone == 1:
			return acl.checkACL(userInfo, connInfo)
		else:
			n2 = node.rfind(".")
			policy = 0
			if n2 != -1:
				policy = self.checkACL(node[:n2], userInfo, connInfo)
			return acl.checkACL(userInfo, connInfo, policy)

OM_BINDINGS = { "OM_XML_CSL":OM_XML_CSL }
