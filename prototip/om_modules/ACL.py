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

# ACL.py
# class for parsing and checking access control lists

# python modules
import xml.dom
import xml.dom.minidom
import pwd, grp

acl_chains = { "User": 0, "Realm": 1, "Group": 2, "Verified": 3, "Crypted": 4, "Caller": 5 }

class ACLRule:
	def __init__(self):
		self.quick = 0
		self.policy = 0
		self.inverse = 0
		self.chain = 0
		self.value = ""

class ACL:
	def __init__(self):
		self.standalone = 0
		self.rules = []
	
	def fromXML(self, xmlstr):
		hede = 0
		if type(xmlstr) is str:
			dom = xml.dom.minidom.parseString(xmlstr)
		else:
			dom = xmlstr
			hede = 1
		tn = dom.getElementsByTagName("acl")
		if not tn:
			return
		acl = tn[0]
		if acl.getElementsByTagName("standalone"):
			self.standalone = 1
			print "standalone"
		for rule in acl.getElementsByTagName("rule"):
			r = ACLRule()
			if rule.getElementsByTagName("quick"):
				r.quick = 1
			tn = rule.getElementsByTagName("policy")[0]
			if tn:
				t = tn.firstChild.data
				if t == "Read only":
					r.policy = 1
				elif t == "Allow":
					r.policy = 2
			if rule.getElementsByTagName("not"):
				r.inverse = 1
			tn = rule.getElementsByTagName("chain")[0]
			if tn:
				t = tn.firstChild.data
				try:
					r.chain = acl_chains[t]
				except:
					pass
			tn = rule.getElementsByTagName("value")[0]
			if tn:
				r.value = tn.firstChild.data[:]
			self.rules.append(r)
		if hede != 1:
			dom.unlink()
	
	def toXML(self):
		return "not implemented"
	
	def fromString(self, s):
		self.standalone = 0
		self.rules = []
		s2 = s.split("\n")
		if s2[0] == "S":
			self.standalone = 1
		for s3 in s2[1:]:
			s4 = s3.split("\t")
			r = ACLRule()
			r.quick = int(s4[0])
			r.policy = int(s4[1])
			r.inverse = int(s4[2])
			r.chain = int(s4[3])
			r.value = s4[4][:]
			self.rules.append(r)
	
	def toString(self):
		if self.standalone == 1:
			s = "S"
		else:
			s = "I"
		for rule in self.rules:
			s += "\n"
			s += str(rule.quick)
			s += "\t"
			s += str(rule.policy)
			s += "\t"
			s += str(rule.inverse)
			s += "\t"
			s += str(rule.chain)
			s += "\t"
			s += rule.value
			return s
	
	def checkACL(self, userInfo, connInfo, parent_policy = 0):
		ret = parent_policy
		for rule in self.rules:
			ok = 0
			# check chain=value
			if rule.chain == 0:
				if rule.value == userInfo.name:
					ok = 1
			elif rule.chain == 1:
				if rule.value == userInfo.realm:
					ok = 1
			elif rule.chain == 2:
				g = getgrgid(getpwuid(userInfo.uid)[3])
				if rule.value == g[0]:
					ok = 1
				else:
					g = None
					try:
						g = getgrnam(rule.value)
					except:
						pass
					if userInfo.name in g[3]:
						ok = 1
			# FIXME: other rules
			# apply not operator
			if rule.inverse == 1:
				if ok == 0:
					ok = 1
				else:
					ok = 0
			# modify policy
			if ok == 1:
				ret = rule.policy
				# test quick exit
				if rule.quick == 1:
					return ret
		return ret

# test
#a = ACL()
#c = ACL()
#b = "<method name='do'><inputs/><acl><standalone/><rule><chain>User</chain><policy>Read only</policy><value>murat</value></rule></acl><description/><description></description></method>"
#a.fromXML(b)
#print a.toString()
#c.fromString(a.toString())
#print c.toString()
#print c.toXML()
#ui = ACLRule()
#ui.name = "murat"
#print c.checkACL(ui,0)
