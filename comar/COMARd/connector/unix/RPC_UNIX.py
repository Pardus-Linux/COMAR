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

# COMARd
# This module provides a connector for COMAR RPC over unix sockets

# global python modules
import os
import socket
import select
import re
import struct
import sys
import pwd

# COMAR modules
import RPCData
import COMARValue
import CHLDHELPER
import traceback

# name of the unix socket which listens incoming connections
rpc_file = "/tmp/comar-test"

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

class UnixRPC:
	conns = []

	def askConn(self,tid):
		ci = RPCData.connectionInfo()
		ci.protocol		= PROTOCOL
		ci.protoAddr 	= "127.0.0.1"	# FIXME: ip/port bilgisi ver
		ci.auth			= 1		# Authenticated
		ci.secure		= 0		# Not secure.
		ci.verify		= 0		# Not verified.
		ci.isStream		= 1		# Yes, keep-alive stream..
		ci.online		= 1		# We are online, currently
		ci.host			= "localhost"	# FIXME: host bilgisi ver
		a = ci.toString()
		print "ci ready:", a
		self.procHelper.sendParentCommand("IRSU_CONN", self.procHelper.myPID, tid, a)
		print "askconn Exit"

	def make_named_pipe(self, name):
		pipe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		try:
			try:
				os.unlink(name)
			except:
				pass
			pipe.bind(name)
		except:
			print "RPC_UNIX: Cannot create listening pipe"
			print "RPC_UNIX: please check and remove the file", name
			sys.exit()
		os.chmod(name, 0666)
		#os.unlink(name)
		pipe.listen(5)
		return pipe
	
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
	
	def handler(self,sock):
		# find connection data
		for conn in self.conns:
			if sock == conn.sock.fileno():
				break
		else:
			print "RPC_UNIX: event from unknown socket?"
		# incoming connection?
		if conn.listen == 1:
			print "RPC_UNIX: incoming connection"
			sock, addr = conn.sock.accept()
			uc = UnixConn()
			uc.sock = sock
			self.conns.append(uc)
			self.askConn(uc.sock.fileno())
			uc.euid, uc.egid = self.getpeereid(uc.sock)
			print "RPC_UNIX peer", uc.euid, uc.egid
		# incoming data?
		else:
			data = conn.sock.recv(4096)
			# connection terminated?
			if data == "":
				# FIXME: baglanti kesilme komutu gonder ta ya
				# self.procHelper.sendParentCommand("INSU_OFF", self.procHelper.myPID, conn.sock.fileno(), 0)
				fd = conn.sock.fileno() + 0
				self.procHelper.delReadHnd(fd)
				#conn.sock.close()
				conn.state = -1
				#self.conns.remove(conn)
			# rpc data?
			else:
				if conn.state == 0:
					# connection not yet allowed by TA manager
					return
				if conn.rpc != None:
					# already processing a rpc call
					return
				print "RPC_UNIX: rpcdata:", data
				conn.buffer += data
				data = conn.buffer
				# parse rpc requests
				t = data.find("<COMARRPCData>")
				if t != -1:
					t2 = data.find("</COMARRPCData>")
					if t2 != -1:
						t3 = data[t:t2+15]
						print "RPC_UNIX: cmd:", t3
						rpc = RPCData.RPCStruct(xmlData=t3)
						if rpc:
							print "unix TTSID:", rpc.TTSID, "CALL:", rpc.Type
						#
						conn.rpc = rpc
						self.procHelper.sendParentCommand("TRSU_CKTA", self.procHelper.myPID, conn.sock.fileno(), rpc.TTSID)
						data = data[t2 + 15:]
						conn.buffer = data

	def cmdHandler(self, From, srcpid, ppid, rfd, pkPid, pkTid, command, pkData):
		print "RPC_UNIX: TA cmd:", command
		# find connection data
		conn = None
		for co in self.conns:
			if pkTid == co.sock.fileno():
				conn = co
				break
		if co == None:
			print "RPC_UNIX: bork bork"
			self.procHelper.sendParentCommand("INSU_OFF", self.procHelper.myPID, pkTid, 0)
			return
		# parse cmd
		if command == "INTU_AUTH":
			print "RPC_UNIX: connAuth"
			user = RPCData.userInfo()
			user.name	= pwd.getpwuid(conn.euid)[0]
			user.realm	= "local"
			user.uid	= conn.euid
			user.group  = ""
			a = user.toString()
			self.procHelper.sendParentCommand("IRSU_AUTH", self.procHelper.myPID, conn.sock.fileno(), a)
		elif command == "INTU_COK":
			print "RPC_UNIX: connOK"
			conn.state = 1
			self.procHelper.addReadHnd(conn.sock.fileno())
		elif command == "LNTU_KILL":
			print "RPC_UNIX: connKill"
			fd = conn.sock.fileno() + 0
			self.procHelper.delReadHnd(fd)
			conn.sock.close()
			self.conns.remove(conn)
			print "New RFDSET:", self.procHelper.extRFDs
		elif command == "TNTU_ARTA":
			print "RPC_UNIX: arta"
			a = conn.rpc.toString()
			self.procHelper.sendParentCommand("TRSU_DATA", self.procHelper.myPID, conn.sock.fileno(), a)
			conn.rpc = None
			if conn.state == -1:
				self.procHelper.sendParentCommand("INSU_OFF", self.procHelper.myPID, conn.sock.fileno(), 0)
				fd = conn.sock.fileno() + 0
				self.procHelper.delReadHnd(fd)
				conn.sock.close()
				self.conns.remove(conn)
		elif command == "TNTU_TANF":
			if conn.rpc.RPCModel() == "new":
				print "RPC_UNIX: TNTU_TANF"
				a = conn.rpc.toString()
				self.procHelper.SendRootCmd("TRSU_RTA", conn.sock.fileno(), a, 0)
			else:
				self.procHelper.sendParentCommand("INSU_OFF", self.procHelper.myPID, conn.sock.fileno(), a)
		elif command == "TRTU_SNDR":
			if conn.state == -1:
				self.procHelper.sendParentCommand("INSU_OFF", self.procHelper.myPID, conn.sock.fileno(), 0)
				fd = conn.sock.fileno() + 0
				self.procHelper.delReadHnd(fd)
				conn.sock.close()
				self.conns.remove(conn)
				return
			print "RPC_UNIX: sndr"
			a = RPCData.RPCStruct()
			a.fromString(pkData)
			x = conn.sock.fileno()
			#print "SOCK INODE:", x, "->", self.procHelper.getfdName(x)
			try:
				conn.sock.send(a.xml)
			except:
				print "Socket Error:", x, "->", self.procHelper.getfdName(x)
			#print "AFTER SEND, SOCK INODE:", x, "->", self.procHelper.getfdName(x)
			self.procHelper.sendParentCommand("LNSU_MCL", self.procHelper.myPID, conn.sock.fileno(), 0)
		return 1

	def serve(self, use_PID, PPID, iochannel):
		print "RPC_UNIX: initializing..."
		self.procHelper = CHLDHELPER.childHelper(iochannel, PPID, use_PID)
		self.procHelper.extRFDHandler = self.handler
		self.procHelper.cmdHandler = self.cmdHandler
		self.procHelper.addSessionCommand(["INTU_COK", "LNTU_KILL", "INTU_AUTH", "TNTU_ARTA", "TRTU_SNDR", "TNTU_TANF"])
		# setup the listening socket
		uc = UnixConn()
		uc.sock = self.make_named_pipe(rpc_file)
		uc.listen = 1
		self.conns.append(uc)
		self.procHelper.addReadHnd(uc.sock.fileno())
		# start listening
		print "RPC_UNIX: listening..."
		while True:
			#print "RPC_UNIX: PIO"
			ret = self.procHelper.ProcessIO()
			if ret == -2:
				print "RPC-UNIX: All childs and channels closed"
				self.procHelper.exit()

			#print "RPC_UNIX: AFTER"

def startServer(ioOBJ, use_PID, PPID, iochannel):
	ioOBJ.serve(use_PID, PPID, iochannel)
	print "RPC-UNIX Start of:", iochannel.name

def stopServer(ioOBJ):
	pass

# modul bilgisi
PROTOCOL = "cxdrpc-unix"
_BLOCKED = True
_KEEPALIVE = True
def getOBJ():
	return UnixRPC()
_OBJ = getOBJ
_START = "startServer"
_STOP = "stopServer"
_CLIENT	= None
