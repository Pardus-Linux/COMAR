# XML-IO-MODULE.
# This module contains COMARRPCoverXML object.

__version__ = "0.1"
__all__ = ["RPCServer"]
# standart python modules
import os
import sys
import select
import posixpath
import cgi
import shutil
import mimetypes
from StringIO import StringIO
import cPickle
import time
import xml.dom.minidom
import copy
import signal
import traceback

# COMAR modules
import comar_global
import RPCData
import COMARValue

session_path = comar_global.session_path
MAX_PIPE_SIZE = 4000
ASKED_CMDS = (hash("TRSU_CKTA"), hash("TNSU_GSID"), hash("IRSU_RTD"), hash("INSU_PID"))
DEBUG_FATAL		= 0
DEBUG_POLL		= 64
DEBUG_IODATA	= 32
DEBUG_PIPEDATA	= 16
DEBUG_CALLDATA	= 8
DEBUG_PIPESYNC	= 4
DEBUG_INIT		= 2
DEBUG_PROCESS	= 1


def _makefilename(org = ""):
        ret = ""
        for i in org:
                if "/*?&%@".find(i) > -1:
                        i = "%%%02x" % ord(i)
                ret += i
        return ret

def stackImage(filt = None, pre = ""):
	tb = traceback.extract_stack()	
	rv = "\n"
	st = 0
	for x in range(len(tb) - 1, -1, -1):
		i = tb[x]
		if i[2].find("stackImage") != -1:
			st = 1			
		elif st and i[2].find("stackImage") == -1:
			a = "%s %s::%s[%s]:'%s'\n" % (pre, os.path.basename(i[0]), i[2], i[1], i[3])
			if filt:
				if i[0] != filt:
					rv += a
			else:
				rv += a
	return rv

class COMARPipe(object):
	"""
		COMAR Pipe.
		Only installed with parent and shared with child. But, child only set
		its own signal handlers after fork() (new session).
	"""
	def __init__(self, dataset = None):
		if dataset == None:
			self.cmdchannel_rx = os.pipe()
			self.cmdchannel_tx = os.pipe()
			self.datachannel_rx = os.pipe()
			self.datachannel_tx = os.pipe()
			self.cmdrpoll = select.poll()
			self.cmdwpoll = select.poll()
			self.datarpoll = select.poll()
			self.datawpoll = select.poll()
			self.cmd_rfile = 0
			self.cmd_wfile = 0
			self.data_rfile = 0
			self.data_wfile = 0
			self.mode = ""
			self.name = ""
		else:
			self.cmdchannel_rx = dataset["crx"]
			self.cmdchannel_tx = dataset["ctx"]
			self.datachannel_rx = dataset["drx"]
			self.datachannel_tx = dataset["dtx"]
			self.cmdrpoll = select.poll()
			self.cmdwpoll = select.poll()
			self.datarpoll = select.poll()
			self.datawpoll = select.poll()
			self.cmd_rfile = dataset["cr"]
			self.cmd_wfile = dataset["cw"]
			self.data_rfile = dataset["dr"]
			self.data_wfile = dataset["dw"]
			self.mode = dataset["mode"]
			self.name = dataset["name"]
			self.cmdrpoll.register(self.cmd_rfile)
			self.cmdwpoll.register(self.cmd_wfile)
			self.datarpoll.register(self.data_rfile)
			self.datawpoll.register(self.data_wfile)

		self.wque = 0
		self.wquePoll = []
		self.debug = 0
		self.debugfile = None
		self.inodes = []
		self.timeout = 0.2

	def getDataSet(self):
		dataset = {}
		dataset["crx"]  = self.cmdchannel_rx
		dataset["ctx"]  = self.cmdchannel_tx
		dataset["drx"]  = self.datachannel_rx
		dataset["dtx"]  = self.datachannel_tx
		dataset["cr"]   = self.cmd_rfile
		dataset["cw"]   = self.cmd_wfile
		dataset["dr"]   = self.data_rfile
		dataset["dw"]   = self.data_wfile
		dataset["mode"] = self.mode
		dataset["name"] = self.name
		return dataset

	def clientReadFD(self):
		return self.cmdchannel_tx[0]

	def clientWriteFD(self):
		return self.cmdchannel_rx[1]

	def parentReadFD(self):
		return self.cmdchannel_rx[0]

	def parentWriteFD(self):
		return self.cmdchannel_tx[1]

	def clientReadD(self):
		return self.datachannel_tx[0]

	def clientWriteD(self):
		return self.datachannel_rx[1]

	def parentReadD(self):
		return self.datachannel_rx[0]

	def parentWriteD(self):
		return self.datachannel_tx[1]

	def initFor(self, mode="parent"):
		if self.mode != "":
			return
		self.mode = mode
		if mode == "parent":
			os.close(self.cmdchannel_rx[1])
			os.close(self.cmdchannel_tx[0])
			os.close(self.datachannel_rx[1])
			os.close(self.datachannel_tx[0])
			self.cmd_rfile = self.cmdchannel_rx[0]
			self.cmd_wfile = self.cmdchannel_tx[1]
			self.data_rfile = self.datachannel_rx[0]
			self.data_wfile = self.datachannel_tx[1]
		elif mode == "root":
			self.cmd_rfile = self.cmdchannel_rx[0]
			self.cmd_wfile = self.cmdchannel_rx[1]
			self.data_rfile = self.datachannel_rx[0]
			self.data_wfile = self.datachannel_rx[1]
		else:
			os.close(self.cmdchannel_rx[0])
			os.close(self.cmdchannel_tx[1])
			os.close(self.datachannel_rx[0])
			os.close(self.datachannel_tx[1])
			#
			# Cross connect pipes
			#
			self.cmd_wfile = self.cmdchannel_rx[1]
			self.cmd_rfile = self.cmdchannel_tx[0]
			self.data_wfile = self.datachannel_rx[1]
			self.data_rfile = self.datachannel_tx[0]

		self.inodes = { "cr":os.readlink("/proc/self/fd/%s" % (self.cmd_rfile)),
						"cw":os.readlink("/proc/self/fd/%s" % (self.cmd_wfile)),
						"dr":os.readlink("/proc/self/fd/%s" % (self.data_rfile)),
						"dw":os.readlink("/proc/self/fd/%s" % (self.data_wfile)) }
		self.debugout(DEBUG_FATAL, "initialization pipeset with: cr:%s cw:%s dw:%s dr:%s" % (os.readlink("/proc/self/fd/%s" % (self.cmd_rfile)),
				os.readlink("/proc/self/fd/%s" % (self.cmd_wfile)),
				os.readlink("/proc/self/fd/%s" % (self.data_wfile)),
				os.readlink("/proc/self/fd/%s" % (self.data_rfile))))
		self.cmdrpoll.register(self.cmd_rfile)
		self.cmdwpoll.register(self.cmd_wfile)
		self.datarpoll.register(self.data_rfile)
		self.datawpoll.register(self.data_wfile)

	def debugout(self, level=0, *msg):
		if (level == DEBUG_FATAL) or (level & self.debug) > 0:
			if self.debugfile:
				f = open("ioch-%s.log" % os.getpid(), "a")
				m = "%s %s %s " % (self.name, self.mode, os.getpid())
				#print self.name, self.mode, os.getpid(),
				for i in msg:
					m = m + " " + str(i)
					#print i,
				#print
				f.write(m+"\n")
				f.close()
			else:
				print "PP:", self.name, self.mode, os.getpid(),
				for i in msg:
					print i,
				print

	def __destroy__(self):
		self.destroy()
	def destroy(self):
		self.debugout(DEBUG_INIT, "Destroyed..")
		#traceback.print_stack()
		try:
			os.close(self.cmd_rfile)
			os.close(self.cmd_wfile)
			os.close(self.data_rfile)
			os.close(self.data_wfile)
		except:
			pass

	def getCommand(self):
		xtry = 5
		while xtry:
			xtry -= 1
			polSt = self.cmdrpoll.poll(1)
			if len(polSt):
				if polSt[0][1] & select.POLLIN:
					try_get = 3
					rd = ""
					while try_get > 0 and rd == "":
						try:
							rd = os.read(self.cmd_rfile, 4)
						except:
							self.debugout(DEBUG_FATAL, "I/O Error. Try recover..")
						if rd == "":
							select.select( [],[],[], 0.1)
						try_get -=1
					if rd == "":
						return None
					size = int(rd)
					if ( size > 0 ):
						cmd = os.read(self.cmd_rfile, size)
						PID = cmd[0:8]
						TID = cmd[8:12]
						CMD = cmd[12:]
						hasData = CMD[1]
						DATA = None
						cmdx = CMD.split(" ")
						if hasData == "R" and len(cmdx) > 1:
							dsize = int(cmdx[1])
							doff  = int(cmdx[2])
							dtot  = int(cmdx[3])
							if dsize == dtot and doff == 0:
								try_get = 3
								rd = ""
								while try_get > 0 and rd == "":
									polSt = select.select([self.data_rfile], [], [], 0.4)
									self.debugout(DEBUG_PIPEDATA, "ReadData Poll Exit fd: %s" % (self.mode))
									if len(polSt) and len(polSt[0]):
										rd = os.read(self.data_rfile, 4)
										try:
											size = int(rd)
										except:
											rd = ""
											rd = os.read(self.data_rfile, 4000)
											self.debugout(DEBUG_FATAL,"Pipe empty:", rd)

									try_get = try_get - 1

								if rd == "":
									return None

								if size != dsize:
									self.debugout(DEBUG_FATAL, "Incorrect data size: channel:%d cmd: '%s' read:'%s' size:'%d' dsize:'%d' pipe:'%s'" % (self.data_rfile, cmd, rd, size, dsize, os.readlink("/proc/self/fd/%s" % (self.data_rfile))))
									while size == 4:
										ok = os.read(self.data_rfile, 4)
										if ok == " OK ":
											rd = os.read(self.data_rfile, 4)
											size = int(rd)
									if size != dsize:
										if self.datarpoll.poll(1)[0][1] & select.POLLIN:
											all = os.read(self.data_rfile, MAX_PIPE_SIZE)
											self.debugout(DEBUG_FATAL, "All Data:", all)
										self.putData(" ERR")
										xtry -= 1
										select.select([self.cmd_rfile],[],[], 1)
										continue

								DATA = os.read(self.data_rfile, dsize)
								self.debugout(DEBUG_PIPEDATA, "READED RAW:", cmd, rd, size, dsize, DATA)
								CMD = CMD.split(" ")[0]
								self.putData(" OK ", "R"+CMD)

							else:
								try_get = 3
								rd = ""
								while try_get > 0 and rd == "":
									polSt = self.datarpoll.poll(1)
									if len(polSt):
										if polSt[0][1] & select.POLLIN:
											rd = os.read(self.data_rfile, 4)
											try:
												size = int(rd)
											except:
												rd = ""
												rd = os.read(self.data_rfile, 4000)
												self.debugout(DEBUG_FATAL,"Pipe empty:", rd)
									try_get = try_get - 1

								if rd == "":
									return None

								if size != dsize:
									self.debugout(0, "Incorrect XTotal data size:", cmd, rd, size, dsize)
									if self.datarpoll.poll(1)[0][1] & select.POLLIN:
										all = os.read(self.data_rfile, MAX_PIPE_SIZE)
										self.debugout(DEBUG_FATAL, "All Data:", all)
									self.putData(" ERR")
									xtry -= 1
									select.select([self.cmd_rfile],[],[], 1)
									continue

								DATA = os.read(self.data_rfile, dsize)
								CMD = CMD.split(" ")[0]
								self.debugout(DEBUG_IODATA, "Read Data Part #1:", CMD, len(DATA), dtot, "(", self.inodes["cr"], ")")
								self.putData(" OK ", "R"+CMD)

								while len(DATA) < dtot:
									rd = ""
									self.debugout(DEBUG_IODATA, "Wait Next Part:", CMD, len(DATA), dtot, "(", self.inodes["cr"], ")")
									polSt = select.select([self.cmd_rfile],[],[], 0.5)
									self.debugout(DEBUG_IODATA, CMD, "Wait Next Part CMD_RFD Return :", polSt, len(DATA), dtot, "(", self.inodes["cr"], ")")
									if len(polSt):
										if len(polSt[0]):
											try_get = 3
											while try_get > 0 and rd == "":
												try:
													rd = os.read(self.cmd_rfile, 4)
												except:
													self.debugout(DEBUG_FATAL, "I/O Error. Try recover..")
												if rd == "":
													select.select( [], [], [], 0.1)
												try_get -=1
											if rd == "":
												return None
											size = int(rd)
											self.debugout(DEBUG_IODATA, CMD, "Wait Next Part cmd size:", rd)
											if ( size > 0 ):
												cmd = os.read(self.cmd_rfile, size)
												self.debugout(DEBUG_IODATA, CMD, "Wait Next Part readed cmd:", cmd)
												PID = cmd[0:8]
												TID = cmd[8:12]
												nCMD = cmd[12:]
												cmdx = nCMD.split(" ")
												if len(cmdx) > 1:
													dsize = int(cmdx[1])
													doff  = int(cmdx[2])
													dtot  = int(cmdx[3])
													if cmdx[0] == "DRTU_DTA":
														#try:
															dfsize = int(os.read(self.data_rfile, 4))
															exDATA = os.read(self.data_rfile, dfsize)
															DATA += exDATA
															rt = self.putData(" OK ", "R"+CMD[2])
															size = len(DATA)
															self.debugout(DEBUG_IODATA, CMD, "Read data part:", dfsize, size, rt)
														#except:
														#	self.debugout(DEBUG_FATAL, "DRTU_DTA pörtledi:")

								self.debugout(DEBUG_IODATA, CMD, "data readed:", len(DATA), dtot)

								if len(DATA) != dtot:
									self.debugout(DEBUG_FATAL, "Incorrect data size:", cmd, rd, size, dsize, DATA, len(DATA), "!=", dtot, os.readlink("/proc/self/fd/%s" % (self.data_rfile)))
									if self.datarpoll.poll(1)[0][1] & select.POLLIN:
										all = os.read(self.data_rfile, MAX_PIPE_SIZE)
										self.debugout(DEBUG_FATAL, "All Data:", all)
									self.putData(" ERR")
									xtry -= 1
									select.select([self.cmd_rfile],[],[], 1)
									continue
						else:
							CMD = CMD.split(" ")[0]
							self.putData(" OK ")

						self.wque = 0
						if len(self.wquePoll):
							self.wquePoll.pop()
						self.debugout(DEBUG_IODATA, "XDBGetCommand pid: %s tid: %s cmd: %s inode-cr: %s" % (PID, TID, CMD, self.inodes["cr"]))
						if CMD in ["LNTU_KILL","TRSU_FIN", "TRTU_FIN"] and self.name.find("HTTP") == -1 and 1==0:
							pre = CMD + " " + str(os.getpid())
							self.debugout(DEBUG_FATAL, "Special Condition: ", CMD," Captured ! from pipe:%s pid:%s" % (self.inodes["cr"], PID), stackImage(__file__, pre) )

						return (PID, TID, CMD, DATA)

		return None

	def putCommand(self, command, pid=0, tid=0, data=None, wait=0):
		xtry = 5
		self.debugout(DEBUG_IODATA, "XDBGPutCommand: pid: %s tid: %s cmd: %s cr: %s cw: %s" % (pid, tid, command, self.inodes["cr"], self.inodes["cw"]))
		if command in ["LNTU_KILL", "TRSU_FIN", "TRTU_FIN"] and self.name.find("HTTP") == -1 and 1==0:
			pre = command + " " + str(os.getpid())
			self.debugout(DEBUG_FATAL, "XDBGPutCommand: pid: %s cmd: %s pipe:%s from %s" % (pid, command, self.inodes["cw"], stackImage(__file__, pre)))

		while xtry:
			polSt = self.cmdwpoll.poll(1)
			remain = 0
			total = 0
			if len(polSt):
				if polSt[0][1] & select.POLLOUT:
					size = len(command)
					offset = 0
					if (size > 0 ):
						if wait:
							self.wque = time.time() + wait
							self.wquePoll.append(command)
						cmd = "%08d%04d%s" % (pid, tid, command)
						if data != None and data != "" and command[1] == "R":
							total = len(data)
							if total > MAX_PIPE_SIZE:
								size = MAX_PIPE_SIZE
								remain = total - size
							else:
								size  = total
								remain = 0
							offset = 0
							cmd = "%s %d %d %d" % (cmd, size, offset, total)
							self.putData(data[:size])
							#data = data[size:]
							offset = size
						size = len(cmd)
						cmd = "%04d%s" % (size, cmd)
						self.debugout(DEBUG_PIPESYNC, "COMMAND TO:", cmd, "( CW:", os.readlink("/proc/self/fd/%s" % (self.cmd_wfile)), ", DW:",os.readlink("/proc/self/fd/%s" % (self.data_wfile)),")")
						size = os.write(self.cmd_wfile, cmd)
						self.debugout(DEBUG_PIPESYNC, "WAIT ACK DATA FOR '%s'" % (command) , "FROM FD", self.data_rfile, ":", os.readlink("/proc/self/fd/%s" % (self.data_rfile)))
						while 1:
							try:
								rt = select.select([ self.data_rfile ], [], [], 0.8)
								break
							except:
								self.debugout(DEBUG_FATAL,"Select failure :(")
								select.select([], [], [], 1)
						self.debugout(DEBUG_PROCESS, "SELECT FOR: ", command, rt, self.data_rfile)
						if len(rt[0]):
							res = os.read(self.data_rfile, 8)
							self.debugout(DEBUG_PIPESYNC, "ACK DATA FROM FD", self.data_rfile, ":", res,"(", os.readlink("/proc/self/fd/%s" % (self.data_rfile)), ")")
							if len(res) == 8 and res[4:8] == " OK ":
								self.debugout(DEBUG_PIPESYNC, "ACK DATA REACHED &OK& '%s'" % (command) , "FROM FD", self.data_rfile, ":", os.readlink("/proc/self/fd/%s" % (self.data_rfile)))
								while remain:
									if remain > MAX_PIPE_SIZE:
										size = MAX_PIPE_SIZE
										remain = remain - size
									else:
										size  = remain
										remain = 0
									cmd = "%08d%04d%s" % (pid, tid, "DRTU_DTA")
									cmd = "%s %d %d %d" % (cmd, size, offset, total)
									csize = len(cmd)
									cmd = "%04d%s" % (csize, cmd)
									nd = data[offset:offset+size]
									self.debugout(DEBUG_IODATA, "Send data part: Ofs:%s size:%s datalen:%s partsize: %s inode:%s" % (offset, size, len(data), len(nd), self.inodes["dw"]))
									dfs = self.putData(nd)
									offset += size
									rt = select.select([], [ self.cmd_wfile ], [], 0.5)
									self.debugout(DEBUG_IODATA, "cmd DRTU_DTA:", dfs, "byte of dch,", rt, offset, size, self.inodes["dw"])
									size = os.write(self.cmd_wfile, cmd)
									self.debugout(DEBUG_IODATA, "DRTU_DTA Send ok ", cmd, ", wait for ACK:", offset, size, self.inodes["cw"])
									while 1:
										try:
											rt = select.select([ self.data_rfile ], [], [], 0.5)
											break
										except:
											self.debugout(DEBUG_FATAL, "Select failure :(")
									self.debugout(DEBUG_IODATA, "DRTU_DTA ACK Select:", rt, offset, size, self.inodes["dw"])
									if len(rt[0]):
										res = os.read(self.data_rfile, 8)
										if len(res) == 8 and res[4:8] == " OK ":
											self.debugout(DEBUG_IODATA, "DRTU_DTA ACK Accepted:", offset, size, self.inodes["dw"])
										else:
											self.debugout(DEBUG_FATAL, "Error Return 1")
											return -1
								return total
							else:
								self.debugout(DEBUG_PIPESYNC, "ACK DATA REACHED &INV& '%s'" % (command) , "FROM FD", self.data_rfile, ":", os.readlink("/proc/self/fd/%s" % (self.data_rfile)))
								xtry -= 1
								select.select([],[],[], 0.1)
								continue
				try:
					a =  os.readlink("/proc/self/fd/%s" % (self.data_rfile)), ")"
				except:
					a = "<unknown/closed> )"

				self.debugout(DEBUG_FATAL, "Pipe not ready for putCommand:", polSt[0][1], self.data_rfile, "(", a, "Our Parent pid:", os.getppid())
				self.debugout(DEBUG_FATAL, "While Sending Command:", command, pid, tid, data)
				#traceback.print_stack()
				self.debugout(DEBUG_FATAL, "Error Return 3")
				return None
			self.debugout(DEBUG_FATAL, "Pipe Timeout")
			#traceback.print_stack()
			self.debugout(DEBUG_FATAL, "Error Return 2")
			return -1
		return -2		# Target Error..

	def _isBusy(self):
		return 0 #self.wque > 0

	def _queLen(self):
		return len(self.wquePoll)

	quelen	= property(_queLen, None, None, "Return wait queue length (send command que client count)")
	isBusy	= property(_isBusy, None, None, "Return true if a response waited..")

	def putData(self, data, forw = ""):
		polSt = self.datawpoll.poll(1)
		if len(polSt):
			if polSt[0][1]:
				size = len(data)
				if (size > 0 ):
					cmd = "%04d%s" % (size, data)
					self.debugout(DEBUG_IODATA, "SEND DATA FOR &%s&%s& -> &%s" % (forw, data[:20], self.inodes["dw"]))
					size = os.write(self.data_wfile, cmd)
					if len(cmd) == 8:
						self.debugout(DEBUG_PIPESYNC, "SYN ACK FOR &%s&%s& -> &%s" % (forw, data[:20], os.readlink("/proc/self/fd/%s" % (self.data_wfile))))
					return size
				return -3
			return -2
		return -1

	def pipeEmpty(self):
		polSt = self.cmdrpoll.poll(1)
		if len(polSt):
			if polSt[0][1] & select.POLLOUT:
				return 1
		return 0

	def cmdReady(self):
		polSt = select.select([self.cmd_rfile], [], [], self.timeout)
		self.debugout(DEBUG_POLL, "cmdready poll result is", polSt)
		if len(polSt[0]):
			if self.cmdrpoll.poll(0)[0][1] & select.POLLHUP:
				self.debugout(DEBUG_POLL, "cmdready poll killed")
				return -1				
			self.debugout(DEBUG_POLL, "cmdready poll okay")
			return 1
		self.debugout(DEBUG_POLL, "cmdready poll failed")
		return 0

	def dataReady(self):
		polSt = self.datarpoll.poll(1)
		if len(polSt):
			if polSt[0][1] & select.POLLIN:
				return 1
		return 0

def _testPipe(cmd="TRSU_CKTA", data="serdar"):
	p = COMARPipe()

	x = os.fork()
	if x:
		p.initFor("parent")
		print "Parent: send bytes:"
		data = COMARValue.string_create("Ben bir stringim")
		ps = p.putCommand(cmd, 109, 159, cPickle.dumps(data))
		print "PARENT PUT:", ps
		st = ""
		os.wait()

	else:
		p.initFor("child")
		select.select([p.cmd_rfile], [], [], 10)
		cmd = p.getCommand()
		print "Command:", cmd
		value = cmd[3]
		cv = cPickle.loads(value)
		print "CHILD: CV =", cv, "CVS=", COMARValue.dump_value_xml(cv)
		sys.exit(1)
