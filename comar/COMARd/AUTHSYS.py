#!/usr/bin/python
# -*- coding: utf-8 -*-
# COMARd	- COMAR Framework main VM.
# Copyright (c) 2003-2005 TUBITAK-UEKAE. All Rights Reserved.

# standart python modules
import os
import sys
import signal
import select
import time
import dircache
import md5
import traceback
import copy
import gdbm
import bsddb
import pwd
from errno import *

# COMAR modules
import comar_global # global values for COMAR

class authSystem:
	def __init__(self):
		self.authModules = {}
		self.digestModules = {}
		self.cryptModules = {}
		self.signModules  = {}
		modpath = comar_global.comar_modpath + "/auth"
		dl = dircache.listdir
		is_file = os.path.isfile
		print "Loading Authentication/Crypto/Digest Modules.."
		files = dl(modpath)
		for file in files:
			fname = modpath + "/" + file
			if is_file(fname):
				if file[-3:] == ".py":
					self.loadModule(fname)
	def __digestList(self):
		return self.digestModules.keys()
	def __passwdList(self):
		return self.authModules.keys()
	def __cryptList(self):
		return self.cryptModules.keys()
	def __signList(self):
		return self.signModules.keys()
	
	digestList = property(__digestList, None, None)
	passwdList = property(__passwdList, None, None)
	cryptList = property(__cryptList, None, None)
	signList = property(__signList, None, None)

	def isRemoteKeyRequired(self, algo = ""):
		if self.cryptModules.has_key(algo):
			dm = self.cryptModules[algo]
			ret = dm.remoteKeyRequired(buf, key)[:]
		
	def getBestAsymCrypto(self, methods = []):
		return "RSA-1024"
		
	def getBestSymCrypto(self, methods = []):
		return "BLOWFISH"
		
	def crypt(self, algo="BLOWFISH", buf = "", key = ""):
		if self.cryptModules.has_key(algo):
			dm = self.cryptModules[algo]
			ret = dm.crypt(buf, key)[:]

	def encrypt(self, algo="BLOWFISH", buf = "", key = ""):
		if self.cryptModules.has_key(algo):
			dm = self.cryptModules[algo]
			ret = dm.encrypt(buf, key)[:]
			
	def cryptLevel(self, algo = "BLOWFISH"):
		if self.cryptModules.has_key(algo):
			dm = self.cryptModules[algo]
			ret = dm.CRYPTLEVEL(buf, key)

	def keyModel(self, algo ):
		if self.cryptModules.has_key(algo):
			dm = self.cryptModules[algo]
			ret = dm.KEY_MODEL(buf, key)

	def digest(self, algo="HMAC-MD5", buf = "", key = ""):
		if self.digestModules.has_key(algo):
			dm = self.digestModules[algo]
			dm.new(key)
			dm.add(buf)
			ret = dm.result()[:]
			dm.clear()
			return ret

	def sign(self, algo="RSA-1024", buf = "", key = ""):
		pass

	def authenticate(self, algo = "SYSTEM", user= "", realm="", passwddesc = ""):
		if self.authModules.has_key(algo):
			dm = self.authModules[algo]
			return dm.authenticate(user, passwddesc)
			
	def getPasswdDescriptor(self, algo = "SYSTEM", user= "", realm="", passwddesc = ""):
		return None

	def loadModule(self, module):
		mod = None			#try:
		sys.path.insert(0, os.path.dirname(module))
		file = os.path.basename(module)
		file = file[:file.rfind('.')]
		mod = __import__(file)
		try:
			mod = __import__(file)
		except:
			print "Could not load:", module, file, sys.path
			sys.path.pop(0)
			return None
		sys.path.pop(0)

		arr = {	'DIGEST_CLASSES':(self.digestModules, "AUTH_TYPE", "Message Digest"),
				'PASSWD_CLASSES':(self.authModules, "AUTH_TYPE", "Password Check"),
				'SIGN_CLASSES':(self.signModules, "AUTH_TYPE", "Message Signing API"),
				'CRYPT_CLASSES':(self.cryptModules, "CRYPT_ALGO", "Buffer crypt/encrypt") }
		for i in arr.keys():
			if i in dir(mod):
				mods = getattr(mod, i)
				for obj in mods:
					hook = obj()
					key = getattr(hook, arr[i][1])
					print "\t", arr[i][2], "module for type:", key, "from", "%s.py" % (file)
					arr[i][0][key] = hook
