# XML-IO-MODULE.
# This module contains COMARRPCoverXML object.

__version__ = "0.1"

# standart python modules
import os
import sys
import select
import signal
import posixpath
import urllib
import cgi
import shutil
import mimetypes
from StringIO import StringIO
import time, xml.dom.minidom, copy, pwd
import PAM
from getpass import getpass
import random

comar_path = "/usr/lib/comard"
sys.path.append(comar_path)
# COMAR modules
import comar_global
import RPCData
import COMARValue
import forkedHTTPServer
session_path = comar_global.session_path
import httplib

COMARHELPER = None

class RPC_HTTP_Client:
	def __init__(self, procHelper = None, comarHelper = None, cryptselCallBack=None, authSelCallback=None):
		self.procHelper = procHelper
		self.ch = comarHelper
		self.myuser = ""
		self.myrealm = ""
		self.connection = None
		self.headerList = {}
		self.cryptInfo = {}
		self.digest = {}
		self.useAuthMethod = ""
		self.authMethods = []
		self.peer = ""

	def _userset(self, value = None):
		if value:
			self.myuser = value
			self.headerList["user"] = self.myuser
			return
		return self.myuser

	def _realm(self, value = None):
		if value:
			self.myrealm = value
			self.headerList["realm"] = self.myrealm
			return
		return self.myrealm

	user = property(_userset, _userset, None)
	realm = property(_userset, _userset, None)

	def makeConnection(self, realmAddress = ""):
		self.peer = realmAddress
		conn = httplib.HTTPConnection(realmAddress)
		#except:
		conn.connect()
		conn.putrequest('GET', '/authinfo')
		conn.putheader("X-client-id", "cxdrpc-http/py/1.0")
		conn.putheader("X-client-flags", "HASCRYPT HASDIGEST")
		conn.endheaders()
		response = conn.getresponse()
		print "Response:"
		for i in response.msg.dict.keys():
			print "\t", i, "=>", response.msg.dict[i]

		useCrypts = response.msg.dict["crypt-methods"][:]

		if useCrypts:
			print "We can use crpyt Methods:", useCrypts

		digMethods = response.msg.dict["digest-methods"]
		digKey   = response.msg.dict["digest-key"][:]
		digId	 = response.msg.dict["digest-ttsid"][:]

		conn = httplib.HTTPConnection(realmAddress)
		#except:
		conn.connect()
		self.connection = conn
		self.digest["key"] = digKey
		self.digest["id"] = digId
		self.digest["methods"] = digMethods.strip().split(" ")
		self.digest["use"] = None
		self.authMethods = response.msg.dict["auth-methods"].strip().split(" ")
		self.passwdMethods = response.msg.dict["pwdcheck-methods"].strip().split(" ")
		self.useAuthMethod = None
		self.usePasswdMethod = None
		self.cryptMethods = useCrypts.strip().split(" ")
		self.headerList["user"] = self.user
		self.headerList["realm"] = self.realm
		
		return [self.digest, self.authMethods[:], self.passwdMethods[:], self.cryptMethods[:]]
	
	def setPasswdMethod(self, methodName = ""):		
		# DON't available in DIGEST Auth Method.
		if methodName == "AUTO":
			methodName = "SYSTEM" #self.ch.authhelper.

		if methodName in self.passwdMethods:
			if self.useAuthMethod != "BASIC":
				self.setAuthMethod("BASIC")


	def setPassPhrase(self, passPhrase = ""):
		if self.useAuthMethod != "BASIC":
			return None

	def setDigestMethod(self, methodName = ""):
		if methodName == "":
			return self.headerList["digest-type"]

		self.headerList["digest-type"] = methodName

	def setAuthMethod(self, methodName = ""):
		if methodName == "":
			return self.useAuthMethod
		if methodName == "AUTO":
			if "DIGEST" in self.authMethods:
				methodName = "DIGEST"
			else:
				methodName = "BASIC"

		if methodName in self.authMethods:
			self.useAuthMethod = methodName
			if methodName == "BASIC":
				# We use user:passwd pair.
				# User must set PassPhrase.
				self.headerList["auth-method"] = "BASIC"
				if self.headerList.has_key("digest-type"):
					del self.headerList["digest-type"]
				if self.headerList.has_key("digest-ttsid"):
					del self.headerList["digest-ttsid"]
				
			else: # Digest Auth..	
				self.headerList["auth-method"] = "DIGEST"
				self.headerList["digest-ttsid"] = self.digest["id"]
				
	authMethod = property(setAuthMethod, setAuthMethod, None)

	def setCryptMethod(self, cryptType = ""):
		#if self.connection !=
		pass

	def sendRPC(self, rpc = None):
		xml = rpc.xml
		#try:
		conn = self.connection
		if not conn:
			conn = httplib.HTTPConnection(self.peer)
			conn.connect()

		conn.putrequest('POST', '/')

		for i in self.headerList.keys():
			conn.putheader(i, self.headerList[i])

		if self.useAuthMethod:
			digVal = self.ch.authhelper.digest( algo=self.useAuthMethod, buf = xml + self.digest["key"], key = self.passwd)
			print "Used digest Method:", self.useAuthMethod, self.digest["key"], self.passwd
			conn.putheader("digest-value", digVal)

		conn.putheader("content-length", len(xml))
		conn.endheaders()
		conn.send(xml)
		response = conn.getresponse()
		if response.msg.dict.has_key("content-size"):
			size = int(response.msg.dict["content-size"])
			buf = response.read(size)
		else:
			# Don't keep alive !
			buf = response.read()

		print "Received:", buf
		#print dir(response), dir(response.msg), response.msg.dict
	pass

class RPCServer(forkedHTTPServer.BaseHTTPRequestHandler):
	debugLevel = 0 #32 + 4
	DEBUG_FATAL = 0
	DEBUG_HTTP = 1
	DEBUG_AUTH = 2
	DEBUG_IPC  = 4
	DEBUG_CONN = 8
	DEBUG_CRYPT = 16
	DEBUG_PCMD  = 32

	def debugout(self, level, *msg):
		if (level == self.DEBUG_FATAL) or (level & self.debugLevel) > 0:
			f = open("http-%s.log" % os.getpid(), "a")
			m = "%s " % (os.getpid())
			print self.procHelper.modName, os.getpid(),
			for i in msg:
				#m = m + " " + str(i)
				print i,
			print
			#f.write(m+"\n")
			#f.close()

	def do_POST(self):
		"""Serve a GET request."""
		global COMARHELPER
		server_version = "COMARRPC-HTTP/" + __version__
		if self.headers.has_key("content-length"):
			size = int(self.headers.getheader("content-length"))
		else:
			size = 0
		if size == 0:
			self.send_response(415)
			self.send_header("Content-type", "text/html")
			msg = "<html><head><title>415 - Bad Data format</title></head><body>HTTP/415 Bad Request<br>Unknown POST Data</br></body></html>"
			self.send_header("Content-length", str(len(msg)))
			self.end_headers()
			self.wfile.write(msg)
			self.close_connection = 1
			return
		xdata = self.rfile.read(size)
		cli = self.client_address
		cli_ip = cli[0]
		cli_port = cli[1]
		cli_uid = -1
		cli_name = ""
		cli_realm = ""
		lverify = 0
		if cli_ip == "127.0.0.1":
			cli_str="%s:%s" % (cli_ip, cli_port)
			i = 5
			ln = None
			#while i:
			#	try:
			p = open("/proc/net/tcp")
			ln = p.readlines()
			p.close()
			#print "L=", ln
			p = cli_ip.split(".")
			for i in [0, 1, 2, 3]:
				p[i] = int(p[i])
			ipstr = "%02X%02X%02X%02X:%04X" % (p[3], p[2], p[1], p[0], cli_port)
			#print "Search TCP Conn Table:", ipstr
			del ln[0]
			if len(ln):
				for l in ln:
					l = l.strip()
					#print "Process :", l
					while l.find("  ") > -1:
						l = l.replace("  ", " ")
					n = l.split(" ")
					#print n
					if n[1] == ipstr:
						#print n
						cli_uid = int(n[7])
						pw = pwd.getpwuid(cli_uid)
						cli_name = pw[0]
						cli_realm = "localhost"

		else:
			# We must check a header info, for authentication..
			digType		= self.headers.getheader("digest-type")
			digValue	= self.headers.getheader("digest-value")
			digId 		= self.headers.getheader("digest-ttsid")
			ruser		= self.headers.getheader("user")
			rrealm		= self.headers.getheader("realm")
			self.procHelper.sendParentCommand("INSU_CONN", self.procHelper.myPID, 0, None)
			self.debugout(self.DEBUG_CONN, "Accepted 'B'onnection Auth Info:", digType, ":", digValue, ":", digId)
			#cmd, tid, pkData, loop = 40):
			dta = self.procHelper.SendRootCmd( "IRSU_RTD", 0, "%s %s" % (self.client_address[0], digId))
			if dta:
				tval = dta[3]
				mypass = "testpass"
				res = COMARHELPER.authhelper.digest(algo=digType, buf = xdata + tval, key = mypass)
				if res == digValue:
					self.debugout(self.DEBUG_AUTH, "Authenticaton passed:", ruser, rrealm, digValue, "=", res)
					cli_name = ruser
					cli_uid = 65500
					cli_realm = rrealm
					lverify = 1
		if 0:
			print "PROC HANDLER:", self.procHelper
			print "HEADERS:\n", self.headers
			print "POST Method:", self.path, "::", size

		self.debugout(self.DEBUG_CONN, "User '%s' over '%s' connected from %s:%d" % (cli_name, cli_realm, cli_ip, cli_port), time.time())

		if cli_name == "":
			self.send_response(415)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write("<html><head><title>401 - Authenticaton Required</title></head><body>HTTP/401 No Auth Info<br>You must use COMAR Authenticaton Extension Formats</br></body></html>")
			self.close_connection = 1
			return

		# With hacked forkedHTTPServer implemantation, we are already forked. But this
		# hack only isolate this code and main code.
		# We can work more session implementation for thus.

		# WE ARE A CONNECTOR.
		# WE ARE ALREADY FORKED AND WAITING FOR SENDRESPONSE.
		# WE PERFORM A CAPSULATION FOR ALL ACCEPTED DATA WITH RPCDATA
		# AND SEND TO IT OUR PARENT. OUR LOGICAL PARENT IS NOT LISTENER.
		# LP IS OBJSESS ROOT.
		# THIS IS A BIG PROBLEM..
		lsecure = 0
		msgCryptMethod = self.headers.getheader("crypt-method")
		if msgCryptMethod:
			self.debugout(self.DEBUG_CRYPT, "Crypted xDATA:", msgCryptMethod)
			pubkey = self.headers.getheader("crypt-publickey")
			if pubkey == None:
				pubkey = COMARHELPER.authhelper.digest(algo="HMAC-MD5", buf = mypass, key = "")
			self.debugout(self.DEBUG_CRYPT, "Use key:", pubkey)
			xdata = COMARHELPER.authhelper.encrypt( algo=digType, buf = xdata, key = pubkey)
			lsecure = COMARHELPER.authhelper.cryptLevel( msgCryptMethod )

		rpc = RPCData.RPCStruct(xmlData=xdata)

		if rpc != None and rpc.TTSID == "":
			self.send_response(415)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write("<html><head><title>415 - Bad Data format</title></head><body>HTTP/415 Bad Request<br>You must use CXRPC Data</br></body></html>")
			self.close_connection = 1
			return
		# We can write a small routine for source.
		if cli_uid == 0:
			cli_uid = -1
		user = RPCData.userInfo()
		user.name	= cli_name
		user.realm	= cli_realm
		user.uid	= cli_uid
		user.group  = ""
		self.debugout(self.DEBUG_CONN, "TTSID:", rpc.TTSID, "::: From:", self.address_string(), "CALL:", rpc.Type)
		#msg = rpc.toString()
		#print self.procHelper.WriteFDs
		ci = RPCData.connectionInfo()
		ci.protocol		= PROTOCOL
		ci.protoAddr 	= "%s:%s" % (cli_ip, cli_port)
		ci.auth			= 1		# Authenticated
		ci.secure		= lsecure	# Not secure.
		ci.verify		= lverify	# Not verified.
		ci.isStream		= 1		# Yes, keep-alive stream..
		ci.online		= 1		# We are online, currently
		ci.host			= cli_ip
		ci.CID			= "%s:%s" % (os.getpid(), time.time())
		a = ci.toString()

		# First, we are start a new connection.
		# HTTP/HTTPS Ptorocols, uses one TA for per PID.
		# But, many RPC-SERVER Modules can be use multiple TID's.
		self.procHelper.sendParentCommand("IRSU_CONN", self.procHelper.myPID, 0, a)

		# TA Manager Connector Subsytem can be send TNSU_AUTH" or "LNSU_KILL".
		# if TA Manager don't accept our connection (No TA)

		rv = 1
		while rv:
			x = 0
			lp = 3
			while not x:
				x = self.procHelper.waitForParentCmd()
				lp -= 1
				if lp == 0:
					break
			if lp:
				self.debugout(self.DEBUG_IPC, "Wait for Parent...")
				pcmd = self.procHelper.getParentCommand()
				self.debugout(self.DEBUG_IPC, "HTTPD: Parent send:", pcmd)

				if pcmd == None:
					if len(self.procHelper.ReadFDs) < 2:
						self.debugout(self.DEBUG_IPC, "HTTPD: Parent dead..:", pcmd)
						os._exit(0)
				else:
					cmd = pcmd[2]
					if cmd == "TRTU_SNDR":
						self.debugout(self.DEBUG_PCMD ,"HTTPD: Response Send")
						sdata = RPCData.RPCStruct()
						sdata.fromString(pcmd[3])
						msg = sdata.xml
						self.send_header("Content-type", "text/xml")
						self.send_header("Content-length", str(len(msg)))
						self.end_headers()
						self.wfile.write(msg)
						self.debugout(self.DEBUG_CONN, "HTTPD: Send Job Complete")
						self.procHelper.sendParentCommand("LNSU_MCL", self.procHelper.myPID, int(pcmd[1]))
						#os.kill(parentPid, signum)
					elif cmd == "LNSU_ERR":
						self.send_response(404)
						msg = "<html><head><title>405 - Invalid Transaction</title></head><body>HTTP 1.0/405 Transaction Not found<br>Please check your call</br></body></html>"
						self.send_header("Content-type", "text/html")
						self.send_header("Content-length", str(len(msg)))
						self.end_headers()
						self.wfile.write(msg)
						rv = 0
						self.close_connection = 1
					elif cmd == "LNSU_MCL":
						# Our data accepted. We must inform client..
						if rpc.Priority != "INTERACTIVE":
							nrpc = RPCData.RPCStruct(TTSID="TEMPORARY")
							nrpc.Priority = "NORMAL"
							nrpc.makeRPCData("RESPONSE")
							nrpc["TTSID"] = rpc.TTSID
							nrpc["status"] = "QUEUE"
							msg = nrpc.xml
							if ci.secure:
								self.debugout(self.DEBUG_CRYPT, "Crypting msg..")
								msg = COMARHELPER.authhelper.crypt(algo = msgCryptMethod, buf = msg, key = mypass)
							self.send_header("Content-type", "text/xml")
							self.send_header("Content-length", str(len(msg)))
							self.end_headers()
							self.wfile.write(msg)
							self.debugout(self.DEBUG_CONN, "HTTPD: Job Queued..")
							self.close_connection = 1
							rv = 0
					elif cmd == "TNTU_ARTA":
						# A previously created remote call
						#print "Response For CKTA remote:", rpc.RPCModel()
						if rpc.RPCModel() == "remote":
							a = rpc.toString()
							self.procHelper.sendParentCommand("TRSU_DATA", self.procHelper.myPID, 0, a)
						else:
							self.do_HEAD()
							self.close_connection = 1
							rv = 0
					elif cmd == "TNTU_LOC":
						# A local Session.
						#print "Response For CKTA local"
						if rpc.RPCModel() == "local":
							a = rpc.toString()
							self.procHelper.sendParentCommand("TRSU_DATA", self.procHelper.myPID, 0, a)
						else:
							self.do_GET()
							self.close_connection = 1
							rv = 0
					elif cmd == "TNTU_TANF":
						self.debugout(self.DEBUG_PCMD, "Response For CKTA new:", rpc.RPCModel)
						if rpc.RPCModel() == "new":
							a = rpc.toString()
							self.debugout(self.DEBUG_IPC, "Sending TRSU_RTA to", self.procHelper.myPID,"->", self.procHelper.gloPPid)
							self.procHelper.dumpInfo()
							#cmd, tid, pkData, loop = 40
							self.procHelper.SendRootCmd("TRSU_RTA", 0, a, 0)
							#self.procHelper.SendRootCmd("TRSU_RTA", self.procHelper.myPID, 0, a)
						else:
							self.procHelper.sendParentCommand("INSU_OFF", self.procHelper.myPID, 0, a)
							self.send_response(404)
							self.send_header("Content-type", "text/html")
							self.end_headers()
							self.wfile.write("<html><head><title>404 - Transaction Not found</title></head><body>HTTP 1.0/404 Transaction Not found<br>Please check your call</br></body></html>")
							self.close_connection = 1
							rv = 0
					elif cmd == "TNTU_DATA":
						#print "HTTPD: Send Accepted Data."
						a = rpc.toString()
						self.procHelper.sendParentCommand("TRSU_DATA", self.procHelper.myPID, 0, a)
					elif cmd == "LNTU_KILL":
						# KILL SELF :(
						self.debugout(self.DEBUG_CONN, "HTTPD: Close Connection:", pcmd[2])
						rv = 0
					elif cmd == "INTU_COK":
						# Connection Accepted..
						t = rpc.TTSID
						self.procHelper.sendParentCommand("TRSU_CKTA", self.procHelper.myPID, 0, t)
					elif cmd == "TNTU_CONN":	# Read Connection Info..
						#print "Parent want Connection info.."
						ci = RPCData.connectionInfo()
						ci.protocol		= PROTOCOL
						ci.protoAddr 	= "%s:%s" % (cli_ip, cli_port)
						ci.auth			= 1		# Authenticated
						ci.secure		= 0		# Not secure.
						ci.verify		= 0		# Not verified.
						ci.isStream		= 1		# Yes, keep-alive stream..
						ci.online		= 1		# We are online, currently
						a = ci.toString()
						self.procHelper.sendParentCommand("TRSU_CONN", self.procHelper.myPID, 0, a)
					elif cmd == "INTU_AUTH":
						#print "Send Auth Data:"
						a = user.toString()
						# we use always TID = 0. We don't use multiple calls.
						self.procHelper.sendParentCommand("IRSU_AUTH", self.procHelper.myPID, 0, a)
		self.procHelper.sendParentCommand("INSU_OFF", self.procHelper.myPID, 0, None)

		self.debugout(self.DEBUG_CONN, "HTTPD: END OF REQ - ", self.address_string(), rpc.TTSID, time.time())
		self.close_connection = 1

	def do_HEAD(self):
		"""Serve a HEAD request."""
		self.send_response(405)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write("<html><head><title>400 - Bad Request</title></head><body>HTTP/400 Bad Request<br>You must use POST method </br></body></html>")

	def do_GET(self):
		global COMARHELPER
		self.debugout(self.DEBUG_CONN, "a GET received:")
		if self.path[0] == "/":
			command = self.path[1:]
		else:
			command = self.path
		self.debugout(self.DEBUG_CONN, "GET Headers:\n", self.headers)
		if command == "authinfo":
			cli = self.client_address
			cli_ip = cli[0]
			cli_port = cli[1]
			cli_uid = -1
			cli_name = ""
			cli_realm = ""
			ci = RPCData.connectionInfo()
			ci.protocol		= PROTOCOL
			ci.protoAddr 	= "%s:%s" % (cli_ip, cli_port)
			ci.auth			= 0		# Authenticated
			ci.secure		= 0		# Not secure.
			ci.verify		= 0		# Not verified.
			ci.isStream		= 0		# Yes, keep-alive stream..
			ci.online		= 0		# We are online, currently
			ci.host			= cli_ip
			a = ci.toString()

			# First, we are start a new connection.
			# HTTP/HTTPS Ptorocols, uses one TA for per PID.
			# But, many RPC-SERVER Modules can be use multiple TID's
			ppid = os.getpid()
			self.procHelper.sendParentCommand("INSU_CONN", self.procHelper.myPID, 0, None)
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			availDigs = ""
			for i in COMARHELPER.authhelper.digestList:
				availDigs  += i + " "
			availDigs = availDigs.strip()
			self.send_header("digest-methods", availDigs)
			availPswd = ""
			for i in COMARHELPER.authhelper.passwdList:
				availPswd  += i + " "
			availPswd = availPswd.strip()
			self.send_header("pwdcheck-methods", availPswd)
			self.send_header("auth-methods", "BASIC DIGEST")

			conn_id = "%s%s" % (ppid, int(time.time()))
			random.seed(time.time())
			dig = "%s-%s%s" % (ppid, hex(int(time.time()))[2:], random.random())
			self.procHelper.sendParentCommand(	"IRSU_STD",
												self.procHelper.myPID,
												0,
												"%s %s %s %s" % (self.client_address[0], conn_id, "300", dig))
			self.send_header("digest-key", dig) # a random data for digest.
			self.send_header("digest-ttsid", conn_id) # Our key id. Always return to we.
			self.send_header("digest-ttl", "300") # TTL Value. We track internally.
			a = self.headers.getheader("X-client-flags")
			if a:
				a = " " + a + " "
				if a.find(" HASCRYPT ") > -1:
					availCrypts = ""
					for i in COMARHELPER.authhelper.cryptList:
						availCrypts  += i + " "
					availCrypts = availCrypts.strip()
					self.send_header("crypt-methods", availCrypts) #

			self.end_headers()
			self.wfile.write("<html><head><title>You must use cxdrpc-http client</title></head><body>Your authentication data already send. See http-header information</body></html>")
			self.debugout(self.DEBUG_AUTH, "cxdrpc-http: Client request auth info: ", dig, conn_id, "180 seconds left.")
			self.close_connection = 1
		else:
			self.do_HEAD()

def test(HandlerClass = RPCServer, ServerClass = forkedHTTPServer.HTTPServer):
    forkedHTTPServer.test(HandlerClass, ServerClass)

def startServer(ioOBJ, use_PID, PPID, iochannel):
	ioOBJ.setCOMARExtensions(use_PID, PPID, iochannel)
	iochannel.sel_timeout = 0.5
	print "WARNING: cxdrpc-http connector: This connector currently support digest based and local socket based auth !"
	ioOBJ.serve_forever()

def stopServer(ioOBJ):
	ioOBJ.server_terminate()


# PROTOCOL: What This moduls served protocol
PROTOCOL = "cxdrpc-http"

# _BLOCKED: Can be blocked IO. if True, COMARd sent a KILLSELF and after 1 second send a SIGTERM.
#	    Normally, COMARd never close a connector module, expect shutdown phase..
_BLOCKED = True

# _KEEPALIVE Supported
_KEEPALIVE = True

def _GetOBJ():
	return forkedHTTPServer.ioObject(HandlerClass = RPCServer, ServerClass = forkedHTTPServer.HTTPServer)
# _OBJ:	Object for IO Module..
_OBJ = _GetOBJ

# _START: method name for start serving. This method bounded to module level (may be).
#	   Its always called with _OBJ, PID for use inside _OBJ, Its own PID (COMARd PID = 0) and a COMARPipe parameters.
_START = "startServer"

# _STOP: method name for stop serving. This method bounded to module level (may be).
#	 Its always called with _OBJ parameter.
_STOP = "stopServer"	# But, _BLOCKED is ready, COMAR Send a "KILLSELF" and a SIGTERM Signal :(

# Client. Client mode protocol Driver.
_CLIENT	= RPC_HTTP_Client
