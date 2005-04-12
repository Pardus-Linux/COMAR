#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2004, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.

# DBWORKER.py
# COMAR Database Related Objects.

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
import socket, struct
from errno import *

# COMAR modules
import comar_global # global values for COMAR
import CHLDHELPER

class DBProvider:
	def __init__(self, name):
		self.db	= None
		self.fname = None
		self.name = name
		self.clients = {}
		self.lc = -1
		self.flags = ""		

	def open(self, file, flags=""):
		#print "DB OPEN:", file,
		#try:
		#	print os.stat(file)
		#except:
		#	print "New File"
		self.fname = file
		self.db = bsddb.btopen(file, "w")
		#print self.db
		#print file, "DB Keys:"
		#for i in self.db.keys():
		#	print i, "=", self.db[i]
		self.flags = flags

	def removeClient(self, client):
		if self.clients.has_key(client):
			del self.clients[client]

	def initClient(self, client):
		try:
			ret = self.db.first()
			self.clients[client] = ret[0]
		except:
			self.clients[client] = -1
			return

	def read(self, client, key):		
		if self.db.has_key(key):			
			self.clients[client] = key
			self.lc = client
			#print self.db[key]
			return self.db[key]		
		return None

	def has_key(self, client, key):
		return self.db.has_key(key)

	def write(self, client, key, data):
		#print "DB WORKER Write operation:", self.fname, key, len(data)
		self.db[key] = data
		self.db.sync()

	def delete(self, client, key):
		if self.db.has_key(key):
			del self.db[key]

	def movefirst(self, client):
		try:
			ret = self.first()
			self.clients[client] = ret[0]
			self.lc = client
			return ret
		except:
			return None

	def movelast(self, client):
		try:
			ret = self.last()
			self.clients[client] = ret[0]
			self.lc = client
			return ret
		except:
			return None

	def seek(self, client, key):
		try:
			ret = self.db.set_location(key)
			self.clients[client] = key
			self.lc = client
		except:
			try:
				ret = self.db.next()
				ret = self.db.previous()
			except:
				return None
		return ret

	def movenext(self, client):
		try:
			key = self.clients[client]
			if self.lc != client:
				ret = self.db.set_location(key)
			ret = self.db.next()
			self.lc = client
		except:
			return None
		self.clients[client] = ret[0]
		return ret

	def moveprev(self, client):
		try:
			key = self.clients[client]
			if self.lc != client:
				ret = self.db.set_location(key)
			ret = self.db.previous()
			self.lc = client
		except:
			return None
		self.clients[client] = ret[0]
		return ret

	def close(self, key):
		self.db.close()

class dbIO:
	def __init__(self):
		self.dbs = {}
	def new(self, client, file, fds):
		fi = hash(file)
		if self.dbs.has_key(fi):
			self.dbs[fi].initClient(client)
			#print "DB File Ready:", client, file
			return fi
		db = DBProvider(str(fi))
		db.open(file)
		db.initClient(client)
		self.dbs[fi] = db
		fds.append(db)
		#print "New DB File:", client, file
		return fi
	def __getitem__(self, index):
		if 	self.dbs.has_key(index):
			return self.dbs[index]
	def close(self, client, file):
		if 	self.dbs.has_key(index):
			self.dbs.removeClient(client)

def db10tuple(dbstr):
	if dbstr == None:
		return None
	x = dbstr.find("=")
	e = dbstr.find("\x01",x + 1)
	hnd = int(dbstr[x + 1: e])
	x = dbstr.find("=", e+1)
	e = dbstr.find(" ",x + 1)
	ksize = int(dbstr[x+1:e])
	key = dbstr[e + 1: e+ksize+1]
	x = dbstr.find("=", e+ksize+1)
	e = dbstr.find(" ",x + 1)
	dsize = int(dbstr[x+1:e])
	val = dbstr[e + 1: e+dsize+1]
	return (key, val, hnd)
	
def dbIOCmdProc(dbobj, conPID, PID, TID, cmd, data, fdtable):
	# return (PID, TID, CMD, DATA)
	#print "New DB Command:", conPID, PID, TID, cmd, data
	if cmd == "QRSU_OPEN":
		hnd = dbobj.new(PID, data, fdtable)		
		#print "DB WORKER Open:", PID, data, hnd
		return (PID, TID, "QRTU_QDB", str(hnd))
	elif cmd == "QRSU_GET":
		hnds = data[:data.find(" ")]
		hnd = int(hnds)
		key = data[data.find(" ")+1:]
		res = dbobj[hnd].read(PID, key)
		#print "DB WORKER READ:", PID, key, res
		if res:
			return (PID, TID, "QRTU_DATA", "HANDLE=%d\x01KEY=%d %s\x01DATA=%d %s\x01"
					% (hnd, len(key), key, len(res), res))
		else:
			return (PID, TID, "QRTU_DATA", None)
	elif cmd == "QRSU_PUT":
		t = db10tuple(data)		
		#print "DB Write Native:", PID, t[0], t[1], t[2]
		res = dbobj[t[2]].write(PID, t[0], t[1])
		return None
	elif cmd == "QRSU_SEEK":
		hnds = data[:data.find(" ")]
		hnd = int(hnds)
		key = data[data.find(" ")+1:]
		res = dbobj[hnd].seek(PID, key)
		if res:
			return (PID, TID, "QRTU_LOC", "HANDLER=%d\x00KEY=%d %s\x00DATA=%d %s\x00"
				% (hnd, len(res[0]), res[0], len(res[1]), res[1]))
		else:
			return (PID, TID, "QRTU_LOC", None)
	elif cmd == "QRSU_NEXT":
		hnd = int(data)
		res = dbobj[hnd].movenext(PID)
		if res:
			return (PID, TID, "QRTU_LOC", "KEY=%d %s\x00DATA=%d %s\x00"
				% (len(res[0]), res[0], len(res[1]), res[1]))
		else:
			return (PID, TID, "QRTU_LOC", None)
	elif cmd == "QRSU_PREV":
		hnd = int(data)
		res = dbobj[hnd].moveprev(PID)
		if res:
			return (PID, TID, "QRTU_LOC", "KEY=%d %s\x00DATA=%d %s\x00"
				% (len(res[0]), res[0], len(res[1]), res[1]))
		else:
			return (PID, TID, "QRTU_LOC", None)
	elif cmd == "QRSU_END":
		#dbobj.
		pass

class localDBHelper:
	def dbOpen(self, fileName):
		return DBIO.new(0, fileName)

	def dbClose(self, dbHandle):
		return

	def dbMoveFirst(self, dbHandle):
		return DBIO[dbHandle].movefirst(0)

	def dbMoveLast(self, dbHandle):
		return DBIO[dbHandle].movelast(0)

	def dbWrite(self, dbHandle, key, data):
		rw = DBIO[dbHandle].write(0, key, data)
		#print "DBWRITE:", DBIO[dbHandle].fname, "Write:", key, len(data), rw
		return rw

	def dbRead(self, dbHandle, key):
		return DBIO[dbHandle].read(0, key)

	def dbSeek(self, dbHandle, key):
		return DBIO[dbHandle].read(0, key)

	def dbNext(self, dbHandle):
		return DBIO[dbHandle].next(0)

	def dbPrev(self, dbHandle):
		return DBIO[dbHandle].prev(0)

class UnixConn:
	def __init__(self):
		self.sock = None
		self.tid = 0
		self.euid = -1
		self.egid = -1
		self.listen = 0
		self.buffer = ""
		self.state = 0
		self.rpc = None

	def fileno(self):
		return self.sock.fileno()

class dbWorker:
	def __init__(self, phelper = None):
		self.iochannel = phelper
		#self.iochannel.name = "DBWORKER"
		self.dbobj = None
		self.DBIO	= dbIO()
		self.sockName = "/tmp/comar-db"
		self.conns = {}
		self.fhnds = {}
		pipe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		try:
			try:
				os.unlink(self.sockName)
			except:
				pass
			pipe.bind(self.sockName)
		except:
			print "DBWORKER: Cannot create listening pipe"
			print "DBWORKER: please check and remove the file", self.sockName
			sys.exit()
		os.chmod(self.sockName, 0666)
		#os.unlink(name)		
		self.socket = pipe
		uc = UnixConn()
		uc.sock = pipe
		uc.listen = 1
		self.conns[0] = uc
		self.socket.listen(25)		

	def getpeereid(self,sock):
		"""getpeereid(sock) -> uid, gid
		Return the effective uid and gid of the remote connection.  Only works on
		UNIX sockets."""
		sizeof_ucred = 12
		format_ucred = 'LLL' # pid_t, uid_t, gid_t
		SO_PEERCRED = 17
		ucred = sock.getsockopt(socket.SOL_SOCKET, SO_PEERCRED, sizeof_ucred)
		pid, uid, gid = struct.unpack(format_ucred, ucred)
		return uid, gid

	def getsocketdata(self):
		pass

	def listen(self):
		sockfd = self.socket.fileno()
		pipefd = self.iochannel.cmd_rfile
		rootfds = [ pipefd, sockfd ]
		self.fhnds[pipefd] = []
		self.iochannel.debug = 0 #255
		self.iochannel.name = "DBWORKERCONN"
		while rootfds:
			try_select = 1
			sockfd = self.socket.fileno()
			pipefd = self.iochannel.cmd_rfile
			rfds = rootfds[:]
			rootfds = [ pipefd, sockfd ]
			cfds = []
			for i in self.conns.keys():
				if i:
					cfds.append(self.conns[i].fileno())
			rfds.extend(cfds)
			while try_select:
				try:
					rds = select.select(rfds, [], rfds, 2)
					try_select = 0
				except:
					print "Warning !!! DB WORKER enter an Invalid State."
					print "\tIPC Channel has broken." % (rfds)
					print "Exiting !.."
					os._exit(0)

			#print "DBWORKER select result:", rfds, rds, self.conns
			if rds:
				if rds[2]:
					print "Closed Connection:", rds
				for rfd in rds[0][:]:
					#print "CH PIO:", rfd, pipefd, sockfd, self.conns
					if rfd == pipefd:
						xready = self.iochannel.cmdReady()
						if xready == 1:
							acc_data = self.iochannel.getCommand() # this is (PID, TID, CMD, DATA) or None
							if acc_data:								
								cmd = acc_data[2]
								PID = int(acc_data[0])
								TID = int(acc_data[1])
								data = acc_data[3]
								#print os.getpid(), "DB WORKER:", cmd, PID, TID
								dTuple = dbIOCmdProc(self.DBIO, 0, PID, TID, cmd, data, self.fhnds[rfd])								
								if dTuple:
									# ORIGINAL: TA_CHLDS.sendCommand(conPID, dTuple = dcmd)
									PID = dTuple[0]
									TID = dTuple[1]
									command = dTuple[2]
									data = dTuple[3]
									#print "DBWORKER: Send",cmd, "response", command, PID, "to", self.iochannel.inodes["cw"]
									self.iochannel.putCommand(command, PID, TID, data, 1)
									#self.stdCmdHandler(cmd, srcpid, ppid, rfd)
						elif xready == -1:
							print "Warning !!! DB WORKER - COMARd pipe fault"
							print "\tIPC Channel has broken." % (rfds)
							print "Exiting !.."
							os._exit(0)
					elif rfd == sockfd:
						# incoming şconnection..
						sock, addr = self.conns[0].sock.accept()
						print "DBWORKER: New Connection:", sock, sock.fileno(), addr
						uc = UnixConn()
						uc.sock = sock
						nsockfd = sock.fileno()
						self.conns[nsockfd] = uc
						self.fhnds[nsockfd] = []
						uc.euid, uc.egid = self.getpeereid(uc.sock)
						#print "DBWORKER UNIX peer", uc.euid, uc.egid
					else:
						# incoming data
						#print "DBWORKER Incoming Data", rfd
						if self.conns.has_key(rfd):
							conn = self.conns[rfd]
							data = conn.sock.recv(8)
							if data == "":
								p = select.poll()
								p.register(sockfd)
								s = p.poll(0)[0][1]
								#print "DBWORKER: Incorrect Connection:", rfd, self.conns[rfd], self.fhnds[rfd], self.fhnds
								#s = self.TAStack[i].IOChannel.cmdrpoll.poll(0)[0][1]
								if s & select.POLLHUP or s & select.POLLNVAL:
									#print "DBWORKER: Socket closed:", rfd
									pass
								self.conns[rfd].sock.close()
								for i in self.fhnds[rfd]:
									i.close()
								del self.fhnds[rfd]
								del self.conns[rfd]					
								continue
							#print "DBWORKER Header From: %d '%s' %d bytes" % (rfd, data, len(data))
							size = int(data)
							data = ""
							while len(data) < size:
								d = conn.sock.recv(size)
								data += d
							if data:
								PID = int(data[0:8])
								TID = int(data[8:12])
								x = data.find(" ", 12)
								cmd = data[12:x]
								if x + 1 != len(data):
									data = data[x+1:]
								else:
									data = None
								#print "\n",os.getpid(), "DB WORKER Socket IO:", cmd, PID, TID, data, "\n"
								#print "DBWORKER Data From: %d Total:%d Read:%d bytes" % (rfd, size, len(data))

								dTuple = dbIOCmdProc(self.DBIO, 0, PID, TID, cmd, data, self.fhnds[rfd])
								if dTuple:
									# ORIGINAL: TA_CHLDS.sendCommand(conPID, dTuple = dcmd)
									PID = dTuple[0]
									TID = dTuple[1]
									command = dTuple[2]
									data = dTuple[3]
									if data == None:
										data = ""
									cmd = "%08d%04d%s " % (PID, TID, command)
									cmd = cmd + data
									data = "%08d%s" % (len(cmd), cmd)
									conn.sock.send(data)
									#print "DBWORKER: Send Data:", data
								else:
									cmd = "%08d%04d%s " % (PID, TID, "QNSU_COK")
									data = "%08d%s" % (len(cmd), cmd)
									conn.sock.send(data)
