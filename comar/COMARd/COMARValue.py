#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2004, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.

# COMARValue
# COMAR Value Management Objects.

# standart python modules
import xml.dom.minidom
import copy
import types

GLO_ENCODING = 'utf-8'
COND_YES = [ "EVET", "evet", "E", "e", "YES", "Y", "y" ]


def structToXML(struct, info, structName):
	dom = xml.dom.minidom.getDOMImplementation()
	doc = dom.createDocument(None, structName, None)
	root = doc.documentElement

	for key in info.keys():
		attr = getattr(struct, key)
		d = info[key]
		node = doc.createElement(key)
		if d[0] == 0:
			val = attr
		else:
			val = attr()
		if d[1] == "I" or d[1] == "N":
			txtNode = doc.createTextNode(val.__str__())
			node.appendChild(txtNode)
		elif d[1] == "V":
			_dump_value_xml(val.__str__(), doc, node)
		root.appendChild(node)
	ret = doc.toxml()
	doc.unlink()
	return ret

class COMARString:
	def __init__(self, encoding=GLO_ENCODING, value = ""):
		self.encoding = encoding
		self.value = value

class COMARArrayItem:
	def __init__(self, arrKey = 0, arrInstance = 0, value = None):
		self.Key = arrKey
		self.Instance = arrInstance
		self.item = value	# Must be a COMARValue
		self.next = None

class COMARObjectDescriptor:
	def __init__(self, objName = "", objClass = "", instanceKey = "", callerInfo = None):
		if callerInfo == None:
			# rebuild from xml?
			self.name = ""
			self.objClass = ""
			self.key = ""
			self.objectData = ""
			self.object = ""
		else:
				
			self.name = objName
			self.objClass = objClass
			self.key = instanceKey
			dom = xml.dom.minidom.getDOMImplementation()
			doc = dom.createDocument(None, "object", None)
			root = doc.documentElement
			node = doc.createElement("objClass")
			txtNode = doc.createTextNode(self.objClass)
			node.appendChild(txtNode)
			root.appendChild(node)
	
			node = doc.createElement("name")
			txtNode = doc.createTextNode(self.name)
			node.appendChild(txtNode)
			root.appendChild(node)
	
			node = doc.createElement("key")
			txtNode = doc.createTextNode(self.key)
			node.appendChild(txtNode)
			root.appendChild(node)
	
			cinode = doc.createElement("callerinfo")
			
			for key in dir(callerInfo):
				if key[0] != "_":
					node = doc.createElement(key)
					val = getattr(callerInfo, key)
					if type(val) == type(""):
						txtNode = doc.createTextNode(val)
						node.appendChild(txtNode)
						cinode.appendChild(node)
					
			root.appendChild(cinode)		
			sd = doc.toxml()+""			
			self.objectData = sd
			self.object = instanceKey

	def fromXml(self, xmlData = "", callerInfo = None):
		doc = xml.dom.minidom.parseString(xmlData)
		print "XML DATA:", xmlData
		if doc == None:
			return none
		#if root == None:
		root = doc.firstChild
		first = root.firstChild
		data = None
		
		while first:
			if first.tagName == "name":
				d = first.firstChild.data[:].encode(GLO_ENCODING)
				self.name = d
			if first.tagName == "objClass":
				d = first.firstChild.data[:].encode(GLO_ENCODING)
				self.objClass = d
			if first.tagName == "key":
				d = first.firstChild.data[:].encode(GLO_ENCODING)
				self.key = d
			if first.tagName == "callerinfo":
				node = first.firstChild
				while node:
					k = node.tagName
					if node.firstChild:
						d = node.firstChild.data[:].encode(GLO_ENCODING)
						setattr(callerInfo, k, d)
					node = node.nextSibling
					
			first = first.nextSibling

def obj_setData(obj = None, data = None, objid = ""):
	""" accept dictionary for data and convert it XML and store to item 'obj.object' """
	dom = xml.dom.minidom.getDOMImplementation()
	doc = dom.createDocument(None, "object", None)
	root = doc.documentElement
	node = doc.createElement("class")
	txtNode = doc.createTextNode(data[key])
	for key in data.keys():
		node = doc.createElement(key)
		txtNode = doc.createTextNode(data[key])
		node.appendChild(txtNode)
		root.appendChild(node)
	obj.object = objid
	sd = doc.toxml()+""	
	return sd
	
def obj_setInstance(obj = None, insstr = ""):
	obj.object = insstr

def obj_getData(obj = None):
	doc = xml.dom.minidom.parseString(obj.object)
	root = doc.firstChild
	first = root.firstChild
	ret = {}
	while first:
		node = first.firstChild
		if node:
			ret[first.tagName] = node.data[:].encode(GLO_ENCODING)
		else:
			ret[first.tagName] = ''
		first = first.nextSibling

	return ret

class COMARObject:
	def __init__(self, home = "", codeBase = "", ):
		self.descriptor = ""
		self.codeBase   = codeBase # 
		
class COMARValue:
	def __init__(self, type = "", data = None):
		self.type = type
		self.data = data
	def destroy(self):
		# dont use directly for maintain compability of C or other langs..
		if self.type == 'array':
			_array_destroy(self)
			del self.type
			del self.data
		elif self.type == 'string':
			del self.data.encoding
			del self.data.value
		elif self.type == 'object':
			pass
		else:
			del self.type
			del self.data

class COMARRetVal:
	def __init__(self, result = 0, value = None):
		self.execResult = result
		self.returnValue = value

def null_create():
	return COMARValue(type='null', data="")
	
def string_create(str = '', encoding = 'utf-8'):
	return COMARValue(type='string', data = COMARString(encoding=encoding, value = str))

def numeric_create(number = 0):
	return COMARValue(type='numeric', data = number.__str__())


def CVAL_destroy(value = None):
	if value == None:
		return 2
	value.destroy()
	return 0

def load_value_xml(str = ''):
	if str == '':
		return None
	doc = xml.dom.minidom.parseString(str)
	root = doc.firstChild
	first = root.firstChild
	#print "TOXML PROC:", dir(first)
	return _load_value_xml(first)


def _load_value_xml(first = None ):
	while first:
		if first.tagName == 'string':
			node = first.firstChild
			strval = node.data[:].encode(GLO_ENCODING)
			x = 0
			p = strval.find("%", x)
			while p > -1:
				if strval[p+1] == "%":
					strval = strval[:p] + strval[p+1:]
					x = p + 1
				else:
					x = p					
					#print strval, p, x, len(strval), strval[p+1:p+3]
					strval = strval[:p] + chr(int(strval[p+1:p+3], 16)) + strval[p+3:]
				p = strval.find("%", x)
			return COMARValue(type='string', data = COMARString(value = strval))

		elif first.tagName == 'numeric':
			node = first.firstChild
			return COMARValue(type='numeric', data = node.data[:].encode(GLO_ENCODING))

		elif first.tagName == 'array':
			node = first.firstChild		#This is <item> tag..
			arr = array_create()
			while node:
				#print node.tagName

				child = node.firstChild
				array_additem(array 	= arr,
							  key      	= node.getAttribute('key').encode(GLO_ENCODING),
							  instance 	= int(node.getAttribute('instance').encode(GLO_ENCODING)),
							  arrValue 	= _load_value_xml(child))
				node = node.nextSibling
			return arr

		elif first.tagName == 'null':
			node = first.firstChild
			return COMARValue(type='null')
		elif first.tagName == "object":
			#self.COMARValue.COMARValue("object", cslVal.value)
			node = first.firstChild
			return COMARValue(type = 'object', data = node.data)

		first = first.nextSibling

def CVALget(value = None):
	if value == None:
		return ""
	if 'item' in dir(value):
		return value.item.data.value
	elif value.type == 'string':
		return value.data.value
	elif value.type == 'numeric':
		return value.data
	elif value.type == 'array':
		return '<array>'
	elif value.type == 'object':
		return '<object>'
	elif value.type == 'null':
		return '<null>'
def dump_value_xml(value = None):
	if value == None:
		print "Invalid value"
		return None

	xml = _dump_value_xml(value)
	txt = xml.toxml()
	xml.unlink()
	return txt

def _dump_value_xml(value = None, doc = None, root = None):
	""" Generic serialization function for value object """
	if value == None:
		return None

	if doc == None or root == None:
		dom = xml.dom.minidom.getDOMImplementation()
		doc = dom.createDocument(None, "root", None)
		root = doc.documentElement

	if value.type == 'array':
		first = value.data
		node = doc.createElement('array')
		root.appendChild(node)
		arrnode = node
		root = root.firstChild

		while first != None:
			node = doc.createElement('item')
			node.setAttribute('key', first.Key[:])
			node.setAttribute('instance', first.Instance.__str__())
			arrnode.appendChild(node)
			newnode = _dump_value_xml(first.item, doc, node)
			#root.appendChild(newnode)
			first = first.next

	elif value.type == 'string':
		node = doc.createElement('string')
		first = value.data
		node.setAttribute('encoding', first.encoding)
		strval = ""
		for i in first.value:
			if i == "%":
				i = "%%"
			elif i > chr(127) or (i in "<>\\[]&") or i < " ":
				i = "%%%02x" % (ord(i))
			strval += i
		txtNode = doc.createTextNode(strval)
		node.appendChild(txtNode)
		root.appendChild(node)

	elif value.type == 'object':
		node = doc.createElement('object')
		print "\tToXML:", value, value.type, value.data
		txtNode = doc.createTextNode(value.data)
		node.appendChild(txtNode)
		root.appendChild(node)

	elif value.type == "numeric":
		node = doc.createElement('numeric')
		#print value.data
		txtNode = doc.createTextNode(value.data)
		node.appendChild(txtNode)
		root.appendChild(node)
	else:
		node = doc.createElement('null')
		root.appendChild(node)		
	return doc


def array_create():
	return COMARValue(type='array')

def array_destroy(array = None):
	""" Destroy all items and main object of 'array' """
	if array == None:
		return 2
	_array_destroy(array)
	array.type = 'null' # Change type for stop recursion..
	array.destroy()

def _array_destroy(array = None):
	""" Destroy all items of 'array' - wrapper function """
	if array == None:
		return 2

	node = array.data
	if array.type != 'array':
		return 1

	while node != None:
		del node.Key
		del node.Instance
		nnode = node.next
		node.item.destroy()
		del node.next
		del node
		node = nnode

def array_additem(array=None, key='', instance=0, arrValue=None):
	first = array.data
	if first == None:
		array.data = COMARArrayItem(arrKey = key, arrInstance = instance, value = arrValue)
		return 0

	while first != None:
		root = first
		first = first.next

	root.next = COMARArrayItem(arrKey = key, arrInstance = instance, value = arrValue)

def array_setitem_value(arrItem = None, value = None):
	if arrItem == None:
		return 2

	CVAL_destroy(arrItem.item)
	arrItem.item = value

def array_setitem_str(arrItem = None, str = ''):
	if arrItem == None:
		return 2

	CVAL_destroy(arrItem.item)
	arrItem.item = string_create(str)

def array_setitem_num(arrItem = None, num = ''):
	if arrItem == None:
		return 2

	CVAL_destroy(arrItem.item)
	arrItem.item = numeric_create(num)

def array_delitem(array=None, key='', instance=0):
	first = array.data
	if first == None:
		return 2

	prev = None

	while first != None:
		if first.Key == key and first.Instance == instance:
			if prev != None:
				prev.next = first.next
			else:
				array.data = first.next

			del first.Key
			del first.Instance
			first.value.destroy()
			break

		prev = first
		first = first.next

	return 0

def array_finditem(array = None, key = '', instance = 0):
	first = array.data
	if first == None:
		return None
	while first != None:
		if first.Key == key and first.Instance == instance:
			return first
		first = first.next

def array2Dict(arr = None):
	if arr == None:
		return {}
	ret = {}
	if arr.type == 'array':
		first = arr.data
		while first != None:
			it = []
			key = first.Key[:]
			v = {}
			tp = first.item.type
			v['type'] = tp
			if tp == "array":
				newnode = array2Dict(first.item)
				
			elif tp == "object":
				newnode = "object" # We must set this to obj descriptor.
				
			elif tp == "string":
				newnode = first.item.data.value
				
			else:
				newnode = first.item.data
				
			v['value'] = newnode
			it.append(v)
			ret[key] = it
			first = first.next
	return ret
	
def gettype(value = None):
	return value.type
def getPrmVal(prms = {}, prmname = "", default = None):
	if prms.has_key(prmname):
		cv = prms[prmname]
		if cv.type == "array":
			val = array2Dict(cv)
		elif cv.type == "object":
			val = cv.data
		else:
			val = CVALget(cv)
		return (cv.type, val)
	else:
		return default

def getValue(value = None):
	p = {"0":value}
	return getPrmVal(p, "0")

def string_boolval(cond_str):
	global COND_YES
	if cond_str in COND_YES:
		return True
	else:
		return False
