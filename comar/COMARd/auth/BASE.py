#!/usr/bin/python
# -*- coding: utf-8 -*-
# COMARd	- COMAR Framework main VM.
# Copyright (c) 2003-2005 TUBITAK-UEKAE. All Rights Reserved.

# standart python modules
import md5
import sha
import hmac
import PAM

from Crypto.Cipher import Blowfish
from Crypto.PublicKey import RSA
from paramiko import ber, rsakey

from errno import *

# AUTH_TYPE   : Authentication provider Type.
#  MSG_DIGEST : Create Hash for a buffer with use "key".
#  PASSWD     : Accept a user/password and authenticate it.
#  MSG_SIGNER : Accept a buffer and sign it / verify it with use in-buffer sign info (such as PGP)
#  CRYPT      : Allow a buffer and crypt/decrypt it with a "public/private key".

class hmacBase:
	def __init__(self, usemod = None, name = ""):
		self.hmac = hmac
		self.mod  = usemod
		self.curr = None
		self.digName = name
		self.AUTH_TYPE = name
	def clear(self):
		self.curr = None
	def new(self, key):
	    self.curr = self.hmac.new(key, "", self.mod)
	def add(self, msg):
		self.curr.update(msg)
	def result(self):
		return self.curr.hexdigest()

def authHMAC_MD5():
	return hmacBase(md5, "HMAC-MD5")

def authHMAC_SHA1():
	return hmacBase(sha, "HMAC-SHA1")

def pamAuth():
	return _pamAuth("")

def plain():
	return _plain()
	
def blowfish():
	return _Blowfish()

def rsa_1024():
	return _rsa_1024()

class _plain:
	CRYPT_ALGO = "PLAIN"
	KEY_MODEL  = "SYMETRIC"
	CRYPTLEVEL = 0
	def __init__(self):
		pass
	def crypt(self, buf, key):
		return buf
	def encrypt(self, buf, key):
		return buf
	def generateFrom(self, passphrase=""):	
		return ("", "")
	def generate(self):
		return ("", "")
	def remoteKeyRequired(self):
		return 0

class _Blowfish:
	CRYPT_ALGO = "BLOWFISH"
	KEY_MODEL  = "SYMETRIC"
	CRYPTLEVEL = 128	
	def __init__(self):
		self.engine = Blowfish
		self.engine.key_size = 128
		self.IV = " " * self.engine.block_size		
	def encrypt(self, buf, key):
		c = self.engine.new(key, self.engine.MODE_ECB, self.IV)
		buf = buf + "."
		x = len(buf)
		r = x % self.engine.block_size
		buf = buf + ( " " * r)
		return c.encrypt(buf)		
	def decrypt(self, buf, key):
		c = self.engine.new(key, self.engine.MODE_ECB, self.IV)
		ret = self.engine.decrypt(buf)
		rval = None
		x = 1
		for i in [ -8, -7, -6, -5, -4, -3, -2, -1]:			
			if ret[i] == ".":
				rval = ret[:len(ret) - x]
				return rval
			elif ret[i] != " ":
				return None
			x += 1
	def generateFrom(self, passphrase=""):	
		return ("12345678", "12345678")
	def generate(self):
		return ("12345678", "12345678")
	def remoteKeyRequired(self):
		return 0
		
class _rsa_1024:
	CRYPT_ALGO = "RSA-1024"
	KEY_MODEL  = "ASYMETRIC"
	CRYPTLEVEL = 65555 + 1024
	def __init__(self):
		pass
	def encrypt(self, buf, key):
		pass
	def decrypt(self, buf, key):
		pass
	def generateFrom(self, passphrase=""):	
		return ("12345678", "12345678")
	def generate(self):
		return ("12345678", "12345678")
	def remoteKeyRequired(self):
		return 1
		

class _pamAuth:
	def __init__(self, service = ""):
		if service == "":
			service = 'passwd'

		self.auth = PAM.pam()
		self.auth.start(service[:])
		self.auth.set_item(PAM.PAM_CONV, self.pam_conv)
		self.passwd = ""
		self.AUTH_TYPE = "SYSTEM"

	def authenticate(self, user = None, realm = "localhost", passwddesc = ""):
		if user != None:
			self.auth.set_item(PAM.PAM_USER, user)
			self.user = user
		else:
			return False
		self.passwd = passwddesc
		try:
			self.auth.authenticate()
			#self.auth.acct_mgmt()
		except PAM.error, (resp, code):
			print 'PAM AUTH: Go away! (%s)' % resp
			return False
		except:
			print 'PAM AUTH: Internal error'
			return False
		else:
			print 'Good to go!'
			return True

	def pam_conv(self, auth, query_list):
		resp = []
		for i in range(len(query_list)):
			query, type = query_list[i]
			if type == PAM.PAM_PROMPT_ECHO_ON:
				resp.append((self.user, 0))
			elif type == PAM.PAM_PROMPT_ECHO_OFF:
				val = self.passwd #getpass(query)
				resp.append((val, 0))
			elif type == PAM.PAM_PROMPT_ERROR_MSG or type == PAM.PAM_PROMPT_TEXT_INFO:
				print query
				resp.append(('', 0));
			else:
				return None
		return resp


DIGEST_CLASSES = [ authHMAC_MD5, authHMAC_SHA1 ]
PASSWD_CLASSES = [ pamAuth ]
SIGN_CLASSES   = []
CRYPT_CLASSES  = [ plain, blowfish, rsa_1024 ]
