##!/usr/bin/python
# -*- coding: utf-8 -*-
# CHILDHELPER	- COMAR IPC Helper.
# Copyright (c) 2003-2005 TUBITAK-UEKAE. All Rights Reserved.

# COMAR modules
import traceback, signal, dircache, socket, dircache
import	SESSION

def dummy_pid():
	return 0

api_select = SESSION.select
api_os = SESSION.os
api_sys = SESSION.sys
api_makepid = dummy_pid
root = None

DEBUG_FATAL = 0
DEBUG_DBIO = 1
DEBUG_CMDIO = 2
DEBUG_CHMGR = 4
DEBUG_CMDS = 8

class childHelper(object):
	"""Child Management API.
	This API provide base communication and process management functions.
	All session providers have this object.
	Initialization:
	\tvar = childHelper(parentIOChannel, parentPID, OurPID)
	"""
	def __init__(self, gloPIO, gloPPid, PID, modName=""):
		TAMGR = childInfo()
		if gloPIO:
			TAMGR.iochannel = gloPIO
			#gloPIO.initFor("child")
		else:
			TAMGR.iochannel = SESSION.COMARPipe()
			if gloPPid == 0:
				TAMGR.iochannel.name = "C_ROOT"
				TAMGR.iochannel.initFor("root")
			else:
				TAMGR.iochannel.initFor("parent")

		TAMGR.iochannel.name = modName
		self.sel_timeout = 20
		self.chlds = {0: TAMGR, gloPPid:TAMGR}
		self.gloPIO = gloPIO
		self.gloPPid = gloPPid
		self.myPID = PID
		self.parentppid	= 0
		self.subchlds = {}
		self.userChecker = None
		self.privData = None
		self.sessionCmds = []
		self.extRFDs = []
		self.extWFDs = []
		self.extXFDs = []
		self.cmdHandler	= None
		self.extRFDHandler = None
		self.dbs = []
		self.debug_pio = 0
		self.ioFaultHandler = self.genIOFault
		self.modName = modName
		self.dbWorker = gloPPid
		self.dbIO = gloPIO
		self.debug = None
		self.dbSocket = None
		self.minChild = 1
		self.pass_cmds = [ "INSU_PID", "IRTU_PID" ]
		self.debugfile = None
		self.debug = 0 #DEBUG_CHMGR

	def setIODebug(self, PID, level, name):
		if self.chlds.has_key(PID):
			self.chlds[PID].iochannel.debug = level
			self.chlds[PID].iochannel.name = name

	def debugout(self, level = 0, *msg):
		if (level == DEBUG_FATAL) or (level & self.debug) > 0:
			if self.debugfile:
				f = open("chlpr.log", "a")
				m = "%s %s %s " % (self.modName, self.myPID, api_os.getpid())
				#print self.name, self.mode, os.getpid(),
				for i in msg:
					m = m + " " + str(i)
					#print i,
				#print
				f.write(m+"\n")
				f.close()
			else:
				print "CH:", self.myPID, self.modName, api_os.getpid(),
				for i in msg:
					print i,
				print

	def dumpInfo(self):
		print self.myPID, "chldhelper info:", self.modName
		print self.myPID, "Parent Info:"
		print self.myPID, "\tParent PID:", self.gloPPid
		if self.gloPIO:
			print self.myPID, "\tParent FDSET:"
			print self.myPID, "\t\t CMD R_FILE: %d ('%s')" % (self.gloPIO.cmd_rfile, self.getfdName(self.gloPIO.cmd_rfile))
			print self.myPID, "\t\t CMD W_FILE: %d ('%s')" % (self.gloPIO.cmd_wfile, self.getfdName(self.gloPIO.cmd_wfile))
			print self.myPID, "\t\tDATA R_FILE: %d ('%s')" % (self.gloPIO.data_rfile, self.getfdName(self.gloPIO.data_rfile))
			print self.myPID, "\t\tDATA W_FILE: %d ('%s')" % (self.gloPIO.data_wfile, self.getfdName(self.gloPIO.data_wfile))
		else:
			print "\tWe are root"
		for i in self.chlds.keys():
			print self.myPID, "Child %d PID: %d OS pid: %d mode:'%s'" % (i, self.chlds[i].PID, self.myPID, self.chlds[i].iochannel.mode)
			print self.myPID, "\t CMD R_FILE: %d ('%s')" % (self.chlds[i].iochannel.cmd_rfile, self.getfdName(self.chlds[i].iochannel.cmd_rfile))
			print self.myPID, "\t CMD W_FILE: %d ('%s')" % (self.chlds[i].iochannel.cmd_wfile, self.getfdName(self.chlds[i].iochannel.cmd_wfile))
			print self.myPID, "\tDATA R_FILE: %d ('%s')" % (self.chlds[i].iochannel.data_rfile, self.getfdName(self.chlds[i].iochannel.data_rfile))
			print self.myPID, "\tDATA W_FILE: %d ('%s')" % (self.chlds[i].iochannel.data_wfile, self.getfdName(self.chlds[i].iochannel.data_wfile))

	def dumpListener(self):
		for i in self.chlds.keys():
			print self.myPID, "\tChild %d PID: %d OS pid: %d mode:'%s'" % (i, self.chlds[i].PID, self.myPID, self.chlds[i].iochannel.mode),
			print self.myPID, "CR: %d ('%s')" % (self.chlds[i].iochannel.cmd_rfile, self.getfdName(self.chlds[i].iochannel.cmd_rfile)),
			print self.myPID, "DR: %d ('%s')" % (self.chlds[i].iochannel.data_rfile, self.getfdName(self.chlds[i].iochannel.data_rfile))

#--------------------------------------------------------------------------------
#	Database Utilities
#--------------------------------------------------------------------------------
	def useDBSocket(self, sockFile = ""):
		if sockFile == "":
			sockFile = "/tmp/comar-db"
		if self.dbSocket:
			self.dbSocket.close()
		self.dbSocket = socket.socket(family = socket.AF_UNIX, type = socket.SOCK_STREAM)
		self.dbSocket.connect_ex(sockFile)
		#print "\n\n",self.modName, "DB Socket I/O:", self.dbSocket, self.dbSocket.fileno(), self.dbSocket.connect_ex(sockFile),"\n\n"
	def sendDBSocket(self, cmd, pid, tid, data):
		if self.dbSocket:
			send_cmd = "%08d%04d%s " % (pid, tid, cmd) + data
			send_data = "%08d%s" % (len(send_cmd), send_cmd)
			#print "\nSend DB Socket:", send_data, "\n"
			try:
				print self.dbSocket.sendall(send_data)
			except:
				self.useDBSocket()

				self.dbSocket.sendall(send_data)
		else:
			self.dbIO.putCommand(cmd, pid, tid, data)

	def getDBrfd(self):
		if self.dbSocket:
			return self.dbSocket.fileno()
		else:
			return self.dbIO.cmd_rfile
	def getDBResult(self):
		if self.dbSocket:
			data = self.dbSocket.recv(8)
			size = int(data)
			data = self.dbSocket.recv(size)
			PID = data[0:8]
			TID = data[8:12]
			x = data.find(" ", 12)
			cmd = data[12:x]
			if x+1 != len(data):
				data = data[x+1:]
			else:
				data = None
			return (int(PID), int(TID), cmd, data, 0)
		else:
			io = self.dbIO
			#print "IO For dbOpen:", io
			srcpid = self.dbWorker
			cmd = io.getCommand()
			if cmd:
				cmd = (cmd[0], cmd[1], cmd[2], cmd[3], srcpid)
			return cmd

	def setDBWorker(self, PID):
		self.dbWorker = PID
		self.dbIO = self.chlds[PID].iochannel

	def QDBProcess(self, cmd, pkPid, pdTid, pkData):
		pass

	def dbOpen(self, fileName):
		tid = (len(self.dbs) - 1) + 1
		self.dbs.append(None)
		self.sendDBSocket("QRSU_OPEN", self.myPID, tid, fileName)
		#dbWorker = self.dbIO
		#dbWorker.putCommand("QRSU_OPEN", self.myPID, tid, fileName)
		loop = 40
		while loop:
			dbrfd = self.getDBrfd()
			rds = api_select.select([dbrfd], [], [], 3)
			if len(rds[0]) == 0:
				print self.modName, "DB Not Ready :", fileName
			else:
				rfd = rds[0][0]
				#io = dbWorker
				#print "IO For dbOpen:", io
				#srcpid = self.dbWorker
				#cmd = io.getCommand()
				cmd = self.getDBResult()
				if cmd:
					pkPid = int(cmd[0])
					pkTid = int(cmd[1])
					ppid = dbrfd
					pkData = cmd[3]
					command = cmd[2]
					srcpid = cmd[4]
					if pkTid == tid and pkPid == self.myPID and command == "QRTU_QDB":
						#print self.modName, self.myPID, "QRTU_QDB Accepted:", cmd
						self.dbs[tid] = int(pkData)
						return tid
					else:
						self.stdCmdHandler(cmd, srcpid, ppid, dbrfd)
			loop -= 1
	def dbClose(self, dbHandle):
		if self.dbs[dbHandle]:
			print "QRSU_END", self.myPID, 0, self.dbs[dbHandle]
			self.sendDBSocket("QRSU_END", self.myPID, 0, str(self.dbs[dbHandle]))
			del self.dbs[dbHandle]
			return self.dbWait("QNSU_COK")

	def dbMoveFirst(self, dbHandle, cmd = "QRSU_FRST"):
		self.sendDBSocket(cmd, self.myPID, 0, self.dbs[dbHandle])
		tid = self.dbWait('QRTU_LOC')
		if tid:
			return tid[1]

	def dbMoveLast(self, dbHandle):
		return self.dbMoveFirst(self, dbHandle, cmd = "QRSU_LAST")

	def dbWrite(self, dbHandle, key, data):
		if self.debug:
			print self.modName, self.myPID, "DB WRITE:", self.dbs[dbHandle], len(key), key, type(data)
		data = "HANDLE=%d\x01KEY=%d %s\x01DATA=%d %s\x01" % (self.dbs[dbHandle], len(key), key, len(data), data)
		#print "QRSU_PUT:", data
		self.sendDBSocket("QRSU_PUT", self.myPID, 0, data)
		return self.dbWait("QNSU_COK")

	def dbRead(self, dbHandle, key):
		if not self.dbs[dbHandle]:
			print "Invalid DB Handler:", dbHandle
			return None
		if self.debug:
			print self.modName, ": GET DB KEY:", dbHandle, self.dbs[dbHandle]
		self.sendDBSocket("QRSU_GET", self.myPID, 0, "%d %s" % (int(self.dbs[dbHandle]), key))
		tid = self.dbWait('QRTU_DATA')
		if tid:
			return tid[1]

	def dbSeek(self, dbHandle, key):
		self.sendDBSocket("QRSU_SEEK", self.myPID, 0, "%d %s" % (self.dbs[dbHandle], key))
		tid = self.dbWait('QRTU_LOC')
		if tid:
			return tid[1]

	def dbNext(self, dbHandle, cmd = "QRSU_NEXT"):
		self.sendDBSocket(cmd, self.myPID, 0, "%d" % (self.dbs[dbHandle], key))
		tid = self.dbWait('QRTU_LOC')
		return tid

	def dbPrev(self, dbHandle):
		return self.dbNext(dbHandle, cmd = "QRSU_PREV")
		pass

	def dbWait(self, waitcmd, loop = 40):
		while loop:
			dbrfd = self.getDBrfd()
			rds = api_select.select([dbrfd], [], [], 1)
			if len(rds[0]) == 0:
				return 0
			cmd = self.getDBResult()
			pkPid = int(cmd[0])
			pkTid = int(cmd[1])
			pkData = cmd[3]
			command = cmd[2]
			srcpid = cmd[4]
			rfd = dbrfd
			if pkTid == 0 and pkPid == self.myPID and command == waitcmd:
				#PID, TID, CMD, DATA
				tid = SESSION.root.db10tuple(pkData)
				return tid
			else:
				if self.dbSocket == None:
					self.stdCmdHandler(cmd, srcpid, pkPid, rfd)
				else:
					print "An Invalid socket I/O", cmd, srcpid, pkPid, rfd, "WAit for:", waitcmd, self.myPID
			loop -= 1
#--------------------------------------------------------------------------------
#	Session Utilities
#--------------------------------------------------------------------------------
	def getUserData(self):
		return self.privData

	def setUserData(self, data):
		self.privData = data
#--------------------------------------------------------------------------------
#	Command Handling
#--------------------------------------------------------------------------------
	def genIOFault(self, p1, p2):
		print "BAD !!! Bad module work :("
		print "IO Fault state handling not used."
		print "On PID %d, iochannel fd %d has broken:\n\texception values: %s" % (self.myPID, p1, p2)
	def SendRootCmd(self, cmd, tid, pkData, loop = 40):
		self.gloPIO.putCommand(cmd, self.myPID, tid, pkData)
		while loop:
			rds = api_select.select([self.gloPIO.cmd_rfile], [], [], 1)
			if len(rds[0]) == 0:
				return 0
			rfd = rds[0][0]
			io = self.gloPIO
			#print "IO For dbMF:", io
			srcpid = self.gloPPid
			ppid = self.parentRFD()
			cmd = io.getCommand()
			pkPid = int(cmd[0])
			pkTid = int(cmd[1])
			pkData = cmd[3]
			command = cmd[2]
			if pkTid == tid and pkPid == self.myPID:
				return cmd
			else:
				self.stdCmdHandler(cmd, srcpid, ppid, rfd)
			loop -= 1

	def waitForParentCmd(self, timeout = 1):
		while 1:
			try:
				res = api_select.select([ self.gloPIO.cmd_rfile ], [], [], timeout)
				break
			except:
				pass
		if res != None and len(res[0]):
			return True
		else:
			return False

	def sendCommand(self, child, command = "", PID = 0, TID = 0, data = None, dTuple = None):
		self.debugout(DEBUG_CMDS, "SCMD:", child, command, PID, TID, data)
		if dTuple != None:
			#(PID, TID, CMD, DATA)
			PID = dTuple[0]
			TID = dTuple[1]
			command = dTuple[2]
			data = dTuple[3]
		wait = 0
		#if hash(command) in SESSION.ASKED_CMDS:
		#	wait = 3
		if not self.chlds.has_key(child):
			if self.subchlds.has_key(child):
				target = self.subchlds[child]
			else:
				print self.modName, api_os.getpid(), self.myPID, "Invalid sendCommand to Child:", child, self.chlds, self.subchlds
				traceback.print_stack()
				return None
		else:
			target	= child
		ret = self.chlds[target].iochannel.putCommand(command, PID, TID, data, wait)
		if ret == None:
			print self.modName, self.myPID, self.gloPPid, "Can't put command to pipe:", command, PID, TID, "CW:", self.chlds[target].iochannel.inodes["cw"]
			fileid = self.chlds[target].iochannel.inodes["cw"]
			dl = dircache.listdir("/proc")
			for f in dl:
				if f[0] in "1234567890":
					dn = "/proc/%s/fd/" % (f)
					fdl = dircache.listdir(dn)
					for l in fdl:
						try:
							if api_os.readlink("%s%s" % (dn,l)) == fileid:
								print "fd Handled on:", f
						except:
							pass

			self.dumpInfo()
			traceback.print_stack()
		if ret < 1:
			return None
		return ret

	def readConn(self, child):
		if not self.chlds.has_key(child):
			if self.subchlds.has_key(child):
				target = self.subchlds[child]
			else:
				print "Invalid readCommand to Child:", child
				return None
		else:
			target	= child
		#print "read TA From: %s %s %s" % (self.chlds[child].iochannel.cmd_rfile,
		#					   self.chlds[child].iochannel.cmdchannel_rx,
		#					   self.chlds[child].iochannel.cmdchannel_tx)
		return self.chlds[target].iochannel.getCommand()

	def getParentCommand(self):
		return self.gloPIO.getCommand()

	def sendParentCommand(self, cmd, pid, tid, data=None):
		#print self.modName, api_os.getpid(), self.myPID, "SEND PARENT COMMAND:", self.gloPPid, cmd, pid, tid
		return self.sendCommand(self.gloPPid, cmd, pid, tid, data)

	def addSessionCommand(self, cmd = None):
		"""ChildHelper trace all communication and process reached commands.
		This function add a command list for internal usage.
		If this commands reached, childHelper call provided cmdHandler command processor.
		"""
		#print "\t\t", self.modName, "PIO Add Session Command:", cmd
		if type(cmd) == type(""):
			self.sessionCmds.append(cmd)
		else:

			if type(cmd) == type([]):
				self.sessionCmds.extend(cmd)
			else:
				return 1
	def clearSessionCommands(self):
		self.sessionCmds = []
	def checkUpCmd(self, dir="P", srcpid=0, cmd="", pktpid=0, tid=0, data=None):
		if dir == "P":	# To parent
			if cmd == "IRSU_APRT":		# Add PID Routing Table
				if data != None:
					self.debugout(DEBUG_CHMGR, "IRSU_APRT Handler:", int(data), "->", srcpid)
					self.registerChild(int(data), srcpid)
			elif cmd == "IRTU_DPRT":	# Remove PID Routing Table.
				if data != None:
					if self.subchlds.has_key(int(data)):
						self.releaseChild(int(data))
		else:			# To Child
			if cmd == "IRSU_APRT":
				if data != None:
					self.debugout(DEBUG_CHMGR, "IRSU_APRT Handler:", int(data), "->", srcpid)
					self.registerChild(int(data), srcpid)			
				
			elif cmd == "IRTU_DPRT":
				if data != None:
					if self.subchlds.has_key(int(data)):
						self.releaseChild(int(data))				
		if self.userChecker:
			return self.userChecker(dir="P", srcpid=0, cmd="", pktpid=0, tid=0, data=None)
		return 0

	def stdCmdHandler(self, cmd, srcpid, ppid, rfd):

		pkPid = int(cmd[0])
		pkTid = int(cmd[1])
		pkData = cmd[3]
		command = cmd[2]
		if rfd != ppid:
			From = "P"
		else:
			From = "C"		
		self.debugout(DEBUG_CMDS, "PIO Captured Command:", command, self.sessionCmds, pkPid, self.myPID)
		if command in self.pass_cmds: #command[0] == "Q":
			# By pass...
			#print self.modName, "PIO Captured Pipe Bypass:", From, command, pkPid, self.myPID
			if From == "C":
				self.debugout(DEBUG_CMDS, "Captured Pipe Command pass client:", From, command, pkPid, self.myPID)
				self.sendCommand(pkPid, command, pkPid, pkTid, pkData)
				return
			else:
				if self.gloPIO:
					self.debugout(DEBUG_CMDS, "Captured Pipe Command pass parent:", From, command, pkPid, self.myPID)
					self.gloPIO.putCommand(command, pkPid, pkTid, pkData)
					return
		else:
			if pkPid == self.myPID or command[2] == 'S':
				if command in self.sessionCmds:
					#print self.modName, "SessionCmd Captured:", command, self.cmdHandler
					self.checkUpCmd(dir=From, srcpid=srcpid, cmd=command, pktpid=pkPid, tid=pkTid, data=pkData)
					if self.cmdHandler:
						ret = self.cmdHandler(From, srcpid, ppid, rfd, pkPid, pkTid, command, pkData)
						if ret == None:
							return -2
						elif type(ret) == type(()):
							self.debugout(DEBUG_CMDS, "From '%s' cmd:'%s' process return: '%s' to '%s'" % (From, command[2], ret[2], ret[0]))
							if ret[0] != 0:
								self.sendCommand(ret[0], ret[1], ret[2], ret[3], ret[4])
							else:
								self.sendParentCommand(command, pkPid, pkTid, pkData)
				else:
					self.checkUpCmd(dir=From, srcpid=srcpid, cmd=command, pktpid=pkPid, tid=pkTid, data=pkData)
				#	return (From, srcpid, ppid, rfd, pkPid, pkTid, command, pkData)
			else:
				if rfd != ppid:
					#print self.modName, self.myPID, "Send To Parent:", pkPid, command
					self.checkUpCmd(dir="P", srcpid=srcpid, cmd=command, pktpid=pkPid, tid=pkTid, data=pkData)
					if cmd:
						self.sendParentCommand(command, pkPid, pkTid, pkData)
				else:
					if cmd:
						self.checkUpCmd(dir="C", srcpid=srcpid, cmd=command, pktpid=pkPid, tid=pkTid, data=pkData)
						#print self.modName, self.myPID, "Send To Child:", self.chlds.keys(), pkPid, command
						if pkPid == 0 and self.myPID == 0:
							#print "Self:", self.gloPPid, self.myPID, self.gloPIO
							self.chlds[0].iochannel.putCommand(command, pkPid, pkTid, pkData)
						else:
							self.sendCommand(pkPid, command, pkPid, pkTid, pkData)

	def ProcessIO(self):
		rfds = self.ReadFDs[:]
		rfds.extend(self.extRFDs)
		try_select = 1
		if self.debug_pio:
			print "Select Entry for ", self.myPID
			for i in rfds:
				a = self.getfdName(i)
				if a[0] == "<":
					print "\tInvalid File Handler:", i
					print "\tCurrent IPC Channels:", self.ReadFDs
					print "\tCurrent External file handlers:", self.extRFDs
				else:
					print "\tFD:", i, "->", a
		if len(rfds) <= self.minChild: # Only Parent PID !
			#print api_os.getpid(), self.myPID, self.gloPPid, "We are lost all childrens and external io channels.."
			return -2
		#dl = dircache.listdir("/proc/self/task/")
		#print "DBGXXX TASKLIST:", api_os.getpid(), dl
		#print "Bridging info for", self.modName, ":"
		#for i in self.chlds.keys():
		#	print self.myPID, "Child %d PID: %d OS pid: %d mode:'%s' name:'%s'" % (i, self.chlds[i].PID, self.myPID, self.chlds[i].iochannel.mode,self.chlds[i].iochannel.name), self.chlds[i].iochannel.inodes

		while try_select:
			try:
				#print self.modName, self.myPID, "SELECT FDS:", rfds
				rds = api_select.select(rfds, self.extWFDs, self.extXFDs, self.sel_timeout)
				try_select = 0
			except:
				for i in rfds:
					a = self.getfdName(i)
					if a[0] == "<":
						if i in self.extRFDs:
							self.ioFaultHandler(i, api_sys.exc_info())
						else:
							print "Warning !!! ChldHelper enter an Invalid State."
							p = self.rfd2PID(i)
							print "\tIPC Channel for Child %d has broken." % (p)
							s = api_os.waitpid(self.chlds[p].ppid, api_os.WNOHANG)
							if api_os.WIFEXITED(s):
								print "\t\tChild is dead !"
							else:
								print "\t\tChild already lived with sys_pid", self.chlds[p].ppid, "try kill it."
								api_os.kill(self.chlds[p].ppid, signal.SIGKILL)
								s = api_os.waitpid(self.chlds[p].ppid, 0)
							self.removeChild(p)
		xsock = 0
		if rds:
			prc = []
			for rfd in rds[0][:]:
				if not ( rfd in prc ):
					prc.append(rfd)
					if rfd in self.extRFDs:
						#print "Ext FD Activity:", rfd, self.extRFDHandler
						xsock = rfd
						if self.extRFDHandler:
							ret = self.extRFDHandler(xsock)
							#print "RFDH Exit:", ret
							if ret == None:
								return -1
					else:
						io = self.readFD2io(rfd)
						if io:
							srcpid = self.rfd2PID(rfd)
							ppid = self.parentRFD()
							cmd = io.getCommand()
							self.debugout(DEBUG_CMDS, "CH PIO:", cmd)
							if io.cmdrpoll.poll(1)[0][1] & api_select.POLLHUP:
								print "iochannel bad!", io.name
								self.removeChild(srcpid)
							else:
								if cmd:
									if cmd[2] in ["LNTU_KILL","TRSU_FIN", "TRTU_FIN"]:
										self.debugout(DEBUG_CMDS, "Special Event: '%s' captured from pipe:%s, can be send to '%s'" % (cmd[2], io.inodes["cr"], self.cmdHandler))
									self.stdCmdHandler(cmd, srcpid, ppid, rfd)
								else:
									print "Invalid command readed.."
									print "\tRead FD SET:", self.ReadFDs
									print "\tExternal Read FD Set:", self.extRFDs
									print "\tSelect returned:", rds
									for io in rds[0]:
										print "\t\t Read FD: %d ('%s')" % (io, self.getfdName(io))
									print "Stack Trace:"
									traceback.print_stack()
						else:
							print "WARNING!! ChldHelper for PID: %d has unstable state." % (self.myPID)
							print "\tRead FD SET:", self.ReadFDs
							print "\tExternal Read FD Set:", self.extRFDs
							print "\tSelect returned:", rds
							for io in rds[0]:
								print "\t\t Read FD: %d ('%s')" % (io, self.getfdName(io))
							print "Stack Trace:"
							traceback.print_stack()

#--------------------------------------------------------------------------------
#	Child Management
#--------------------------------------------------------------------------------
	def registerChild(self, child, parent):
		self.subchlds[child] = parent
		if self.gloPIO:		# if we are not root for tree..
			self.debugout(DEBUG_CHMGR, "New Child Registered :", child, "to ->", parent, "( informed:", self.gloPPid, ")")
			if self.myPID == 7:
				traceback.print_stack()
			self.gloPIO.putCommand("IRSU_APRT", self.myPID, 0, child.__str__())
		else:
			self.debugout(DEBUG_CHMGR, "root: ADD CHILD ENTRY:", child, "->", parent, self.subchlds)

	def getParentOfChild(self, child):
		return self.subchlds[child]
	def releaseChild(self, child):
		if self.subchlds.has_key(child):
			del self.subchlds[child]

	def makeChild(self, imm = 0):
		if self.myPID == 0:
			newPID = api_makepid()
		else:
			newPID = 0
			tc = 0
			while self.gloPIO.isBusy:
				#print "Wait for new PID"
				api_select.select([], [], [], 0.1)
				tc += 1
				if tc == 30:
					print "Parent is too BUSY !"
					break
			#print self.myPID, "New PID request to TAM from", self.modName
			self.gloPIO.putCommand("INSU_PID", self.myPID)

			ready = api_select.select([ self.gloPIO.cmd_rfile ], [], [], 3)			
			if len(ready[0]):
				rpid = self.gloPIO.getCommand()
				# getCommand return: (PID, TID, CMD, DATA)
				#print self.modName, "MC: ", rpid
				if rpid[2] == "IRTU_PID":
					newPID = int(rpid[3])
			if newPID == 0:
				return 0
		chld = childInfo()
		chld.PID = newPID
		chld.iochannel = SESSION.COMARPipe()
		self.chlds[newPID] = chld
		self.debugout(DEBUG_CHMGR, "MC: RDFDSET:",  newPID)
		#                      command, pid=0, tid=0, data=None, wait=0):
		if self.myPID != 0:
			self.gloPIO.putCommand(command="IRSU_APRT", pid=self.myPID, tid=0, data=str(newPID), wait = 3)
			#print "Get PID Result:", newPID, chld, self.ReadFDs, self.chlds
		else:
			self.checkUpCmd(dir="P", srcpid=newPID, cmd="IRSU_APRT", pktpid=newPID, tid=0, data=str(newPID))

		#print "Root New CHILD Result:", newPID, chld, self.chlds
		return newPID

	def removeChild(self, PID):
		if self.chlds.has_key(PID):
			self.chlds[PID].iochannel.destroy()
			del self.chlds[PID]
			if self.gloPIO:
				self.gloPIO.putCommand("IRSU_DPRT", 0, 0, PID.__str__())
			# Delete any sub child routing information, if exist..
			for i in self.subchlds.keys():
				if self.subchlds[i] == PID or i == PID:
					del	self.subchlds[i]

	def exit(self):
		if self.gloPIO:
			print api_os.getpid(), self.myPID, "Killed self. OS Parent:", self.parentppid, self.gloPPid, self.modName
			#traceback.print_stack()
			self.gloPIO.putCommand("IRSU_DPRT", 0, 0, self.myPID.__str__())
			api_select.select([],[],[], 0.1)
		else:
			# We are root
			pass
		print api_os.getpid(), self.myPID, "XXXXXXX Killed self. OS Parent:", self.parentppid, self.gloPPid, self.modName
		#print SESSION.stackImage(__file__)
		api_os._exit(1)
#--------------------------------------------------------------------------------
#	Pipe Handling
#--------------------------------------------------------------------------------
	def initForChild(self, PID):
		if self.chlds.has_key(PID):
			#print "ICHLD:", PID, self.chlds
			self.chlds[PID].iochannel.initFor("child")
			self.chlds[PID].iochannel.name = self.modName
			#if self.chlds[PID].iochannel.datarpoll.poll(0)[0][1] & api_select.POLLIN:
			#	api_os.read(self.chlds[PID].iochannel.data_rfile,128)
			#if self.chlds[PID].iochannel.cmdrpoll.poll(0)[0][1] & api_select.POLLIN:
			#	api_os.read(self.chlds[PID].iochannel.cmd_rfile,128)

	def initForParent(self, PID):
		#d1 print "INIT FP:", PID, self.chlds.has_key(PID), self.chlds
		if self.chlds.has_key(PID):
			#print "IPARENT:", PID, self.chlds
			self.chlds[PID].iochannel.initFor("parent")
			self.chlds[PID].iochannel.name = self.modName
			#if self.chlds[PID].iochannel.datarpoll.poll(0)[0][1] & api_select.POLLIN:
			#	api_os.read(self.chlds[PID].iochannel.data_rfile,128)
			#if self.chlds[PID].iochannel.cmdrpoll.poll(0)[0][1] & api_select.POLLIN:
			#	api_os.read(self.chlds[PID].iochannel.cmd_rfile,128)
			if self.gloPIO:		# if we are not root for tree..
				self.debugout(DEBUG_CHMGR, "New Child Register self with :", PID, "to ->", self.myPID, "( informed:", self.gloPPid, ")")
			else:
				self.debugout(DEBUG_CHMGR, "root: ADD CHILD ENTRY:", PID, "->", self.gloPPid, self.subchlds)

	def addReadHnd(self, fd):
		self.extRFDs.append(fd)

	def delReadHnd(self, fd):
		i = 0
		for x in self.extRFDs:
			if x == fd:
				print "delete",i, x
				self.extRFDs.pop(i)
			i += 1

	def _readFDSet(self):
		ret = []
		for i in self.chlds.keys():
			#if i != self.gloPPid and self.myPID > 0:
			rfd = self.chlds[i].iochannel.cmd_rfile
			rst = self.chlds[i].iochannel.cmdrpoll.poll(0)[0][1]
			if rst == api_select.POLLNVAL or rst == api_select.POLLHUP:
				if self.myPID:
					self.removeChild(i)
			else:
				if not (rfd in ret):
					ret.append(rfd)
				#ret.append(self.chlds[i].iochannel.clientReadFD())
			#else:
			#	print "TTTTT:", self.chlds, ret, self.chlds[i].iochannel.cmd_rfile
			#	self.removeChild(i)
		return ret

	def _writeFDSet(self):
		ret = []
		for i in self.chlds.keys():
			if i != self.gloPPid:
				ret.append(self.chlds[i].iochannel.clientWriteFD())
		return ret

	ReadFDs = property(_readFDSet, None, None, None)
	WriteFDs = property(_writeFDSet, None, None, None)
#--------------------------------------------------------------------------------
#	Pipe and Process Information..
#--------------------------------------------------------------------------------
	def rfd2PID(self, fd):
		"""read fd to process PID"""
		for i in self.chlds.keys():
			if self.chlds[i].iochannel.cmd_rfile == fd:
				return i
	def wfd2PID(self, fd):
		"""write fd to process PID"""
		for i in self.chlds.keys():
			if self.chlds[i].iochannel.cmd_wfile == fd:
				return i
	def ppid2PID(self, fd):
		"""write fd to process PID"""
		for i in self.chlds.keys():
			if self.chlds[i].ppid == fd:
				return i

	def parentWFD(self):
		"""return Parents Write fd"""
		return self.gloPIO.cmd_wfile

	def parentRFD(self):
		"""return Parents Read fd"""
		return self.gloPIO.cmd_rfile

	def PID2io(self, PID):
		"""return Process COMARPipe object"""
		if self.chlds.has_key(PID):
			return self.chlds[PID].iochannel
		print "PID NOT FOUND:", PID, self.chlds.has_key(PID),"in", self.chlds

	def PID2rfd(self, PID):
		"""return Process read fd"""
		if self.chlds.has_key(PID):
			return self.chlds[PID].iochannel.cmd_rfile

	def PID2wfd(self, PID):
		"""return Process write fd"""
		if self.chlds.has_key(PID):
			return self.chlds[PID].iochannel.cmd_wfile

	def readFD2io(self, fd):
		"""return Process COMARPipe object for any read fd"""
		for i in self.chlds.keys():
			if self.chlds[i].iochannel.cmd_rfile == fd:
				return self.chlds[i].iochannel

	def writeFD2io(self, fd):
		"""return Process COMARPipe object for any write fd"""
		for i in self.chlds.keys():
			if self.chlds[i].iochannel.clientWriteFD() == fd:
				return self.chlds[i].iochannel

	def PID2readFD(self, PID):
		"""return Process COMARPipe object"""
		if self.chlds.has_key(PID):
			return self.chlds[PID].iochannel

	def PID2WriteFD(self, PID):
		"""return Process COMARPipe object, same as PID2readFD(PID)"""
		if self.chlds.has_key(PID):
			return self.chlds[PID].iochannel

	def getfdName(self, fd):
		try:
			f = api_os.readlink("/proc/self/fd/%s" % (fd))
		except:
			f = "<unknown/invalid file %d>" % (fd)
		return f

class childInfo:
	def __init__(self):
		self.iochannel = None
		self.ppid = 0
		self.PID = 0
		self.status = 0
		self.type = ""
		self.priData = None
