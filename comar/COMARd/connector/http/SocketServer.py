__version__ = "0.4"

import socket
import sys
import os, traceback, signal, copy, select, time
import SESSION, CHLDHELPER

class BaseServer:

	def __init__(self, server_address, RequestHandlerClass):
		"""Constructor.  May be extended, do not override."""
		self.server_address = server_address
		self.RequestHandlerClass = RequestHandlerClass
		self.serverActive = 0

	def	server_terminate(self):
		self.serverActive = 0
	def server_activate(self):
		"""Called by constructor to activate the server.

		May be overridden.

		"""
		pass

	def serve_forever(self):
		"""Handle one request at a time until doomsday."""
		self.serverActive = 1
		while self.serverActive:
			rfds = self.procHelper.ReadFDs
			sockFile = self.socket.fileno()
			rfds.append(sockFile)
			try_select = 1
			#print "HTTP RFDS:", rfds
			if len(rfds) == 1:
				print "RPC-HTTP: We are lost our parents or socket closed.. Exiting Normally !"
				self.procHelper.exit()
				print "Error.. We can't exit :("

			while try_select:
				try:
					rds = select.select(rfds, [], [], 3)
					try_select = 0
					#print "Connection from:", rds, rfds
				except:
					print "Select Exception. Can be a SIGCHLD ?"

			if rds != None and len(rds) ==  1:
				print "RPC-HTTP: We are lost our parents or socket closed.. Exiting Normally !"
				self.procHelper.exit()
			xsock = 0
			if rds:
				for rfd in rds[0]:
					if rfd == sockFile:
						xsock = rfd
						#print "HTTP Main Loop: Socket I/O"
					else:
						io = self.procHelper.readFD2io(rfd)
						srcpid = self.procHelper.rfd2PID(rfd)
						ppid = self.procHelper.parentRFD()
						cmd = io.getCommand()
						#print self.procHelper.myPID, os.getpid(), "HTTP Main Loop: Read a command:", str(cmd)[:20], ppid, srcpid
						if io.cmdrpoll.poll(1)[0][1] & select.POLLHUP:
							self.procHelper.removeChild(srcpid)
						else:
							pkPid = int(cmd[0])
							pkTid = int(cmd[1])
							pkData = cmd[3]
							command = cmd[2]
							#print "ACCEPT READ FROM PIPE:",rfd, ppid, str(cmd)[:20]
							if rfd != ppid:
								#print "Send To Parent:", pkPid, command
								self.procHelper.checkUpCmd(dir="P", srcpid=srcpid, cmd=command, pktpid=pkPid, tid=pkTid, data=pkData)
								if cmd:
									self.procHelper.sendParentCommand(command, pkPid, pkTid, pkData)
							else:
								if cmd:
									self.procHelper.checkUpCmd(dir="C", srcpid=srcpid, cmd=command, pktpid=pkPid, tid=pkTid, data=pkData)
									#print "Send To Child:", pkPid, command
									self.procHelper.sendCommand(pkPid, command, pkPid, pkTid, pkData)
				if xsock > 0:
					self.handle_request()
			else:
				for i in l:
					try:
						x = os.waitpid(i, os.WNOHANG)
						print "Child info:", i, x
						if os.WIFEXITED(x[1]):
							print "Child Deleted:", i, x
							del l[p]
					except:
						pass

	def handle_request(self):
		"""Handle one request, possibly blocking."""
		try:
			request, client_address = self.get_request()
		except socket.error:
			return
		if self.verify_request(request, client_address):
			try:
				self.process_request(request, client_address)
			except:
				self.handle_error(request, client_address)
				self.close_request(request)

	def verify_request(self, request, client_address):
		"""Verify the request.  May be overridden.

		Return True if we should proceed with this request.

		"""
		return True

	def process_request(self, request, client_address):
		"""Call finish_request.
		Overridden by ForkingMixIn and ThreadingMixIn.
		"""
		self.finish_request(request, client_address)
		self.close_request(request)

	def server_close(self):
		"""Called to clean-up the server.
		May be overridden.
		"""
		pass

	def finish_request(self, request, client_address):
		"""Finish one request by instantiating RequestHandlerClass."""
		self.RequestHandlerClass(request, client_address, self)

	def close_request(self, request):
		"""Called to clean up an individual request."""
		pass

	def handle_error(self, request, client_address):
		"""Handle an error gracefully.  May be overridden.

		The default is to print a traceback and continue.

		"""
		print '-'*40
		print 'Exception happened during processing of request from',
		print client_address
		import traceback
		traceback.print_exc() # XXX But this goes to stderr!
		print '-'*40


class TCPServer(BaseServer):
	address_family = socket.AF_INET
	socket_type = socket.SOCK_STREAM
	request_queue_size = 5
	allow_reuse_address = False
	def __init__(self, server_address, RequestHandlerClass):
		"""Constructor.  May be extended, do not override."""
		BaseServer.__init__(self, server_address, RequestHandlerClass)
		self.socket = socket.socket(self.address_family,
									self.socket_type)
		self.server_bind()
		self.server_activate()

	def server_bind(self):
		"""Called by constructor to bind the socket. May be overridden. """
		if self.allow_reuse_address:
			self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.bind(self.server_address)

	def server_activate(self):
		"""Called by constructor to activate the server. May be overridden. """
		self.socket.listen(self.request_queue_size)

	def server_close(self):
		"""Called to clean-up the server. May be overridden. """
		self.socket.close()

	def fileno(self):
		"""Return socket file number. Interface required by select(). """
		return self.socket.fileno()

	def get_request(self):
		"""Get the request and client address from the socket. May be overridden."""
		return self.socket.accept()

	def close_request(self, request):
		"""Called to clean up an individual request."""
		request.close()

usrhnd = None
def	sigchldhandler(sig, frm):
	global usrhnd
	#print "SIGCHLD:", sig, frm, usrhnd

	if sig == 0:
		usrhnd = frm
		#print "Child Tracker: HTTPD Connection Table:", usrhnd.getUserData()
		return

	if usrhnd:
		l = usrhnd.getUserData()
		if l == None:
			l = []
		p = 0
		#print "Seek child over", l
		for i in l:
			try:
				x = os.waitpid(i, os.WNOHANG)
				#print "Child info:", i, x
				if os.WIFEXITED(x[1]):
					#print "Child Deleted:", i, x
					del l[p]
					srchnd = usrhnd.ppid2PID(i)
					if srchnd:
						#print "Delete PID:", srchnd
						usrhnd.removeChild(srcpid)
			except:
				pass
			p += 1
		usrhnd.setUserData(l)
		#print "New Child Table:", l

	else:
		print "SIGCHLD Arrived, but child table is not ready:"


class ForkingMixIn:

	"""Mix-in class to handle each request in a new process."""

	active_children = None
	max_children = 40

	def collect_children(self):
		"""Internal routine to wait for died children."""
		while self.active_children:
			if len(self.active_children) < self.max_children:
				options = os.WNOHANG
			else:
				# If the maximum number of children are already
				# running, block while waiting for a child to exit
				options = 0
			try:
				pid, status = os.waitpid(0, options)
			except os.error:
				pid = None
			if not pid: break
			self.active_children.remove(pid)

	def process_request(self, request, client_address):
		"""Fork a new subprocess to process the request."""
		#traceback.print_stack()
		self.collect_children()
		chldPID = self.procHelper.makeChild()
		print "HTTP New Connection: Go Fork for accept: ", self.procHelper.PID2io(chldPID), chldPID
		parentrpid = os.getpid()
		pid = os.fork()
		if pid:
			# Parent process
			print "HTTPD Conn Parent:", self.procHelper.myPID ,chldPID
			self.procHelper.setIODebug(chldPID, 0, "HTTP->Connection")
			self.procHelper.initForParent(chldPID)
			self.procHelper.registerChild(chldPID, self.procHelper.myPID)
			sigset = self.procHelper
			self.procHelper.sendCommand(child = chldPID, command = "INTU_MCL", PID = chldPID, TID = 0, data = None)
			try:
				select.select([self.procHelper.PID2rfd(chldPID)], [],[], 0.1)
			except:
				pass
			tp = self.procHelper.readConn(chldPID)
			pid = int(tp[3])
			l = sigset.getUserData()
			if l == None:
				l = []
			l.append(pid)
			sigset.setUserData(l[:])
			sigchldhandler(0, sigset)
			if self.active_children is None:
				self.active_children = []
			self.active_children.append(pid)
			self.close_request(request)
			#print "PID", chldPID, "created ppid:", pid, sigset.getUserData()
			return
		else:
			# Child process.
			# This must never return, hence os._exit()!
			self.procHelper.setIODebug(chldPID, 0, "Connection->HTTP")
			gloPIO = self.procHelper.PID2io(chldPID)
			gloPPid = self.procHelper.myPID + 0
			new_ph = CHLDHELPER.childHelper(gloPIO, gloPPid, chldPID)
			new_ph.setIODebug(chldPID, 0, "Connection->HTTP")
			new_ph.initForChild(gloPPid)
			self.procHelper = new_ph
			self.procHelper.parentppid = parentrpid
			print "HTTPD Conn Child:", chldPID, os.getpid(), self.procHelper.parentppid, self.procHelper.myPID, self.procHelper.gloPPid
			try:
				#print "I am new child:", os.getpid()
				self.procHelper.waitForParentCmd(timeout = 1)
				pcmd = self.procHelper.getParentCommand()
				self.procHelper.sendParentCommand(cmd = "IRSU_PPID", pid = chldPID, tid = 0, data=str(os.getpid()))
				self.finish_request(request, client_address)
				os._exit(0)
			except:
				try:
					self.handle_error(request, client_address)
				finally:
					os._exit(1)

	def	setCOMARExtensions(self, myPID, parentPID, parentIO):
		self.procHelper = CHLDHELPER.childHelper(parentIO, parentPID, myPID, "HTTP-MainLoop")
		self.procHelper.setIODebug(parentPID, 0, "HTTP-MainLoop")
		self.procHelper.initForChild(parentPID)
		signal.signal(signal.SIGCHLD, sigchldhandler)
		print "HTTPD Socket Server: COMAR Ext:", self.procHelper.__class__


class ForkingTCPServer(ForkingMixIn, TCPServer): pass

class BaseRequestHandler:

	"""Base class for request handler classes.

	This class is instantiated for each request to be handled.  The
	constructor sets the instance variables request, client_address
	and server, and then calls the handle() method.  To implement a
	specific service, all you need to do is to derive a class which
	defines a handle() method.

	The handle() method can find the request as self.request, the
	client address as self.client_address, and the server (in case it
	needs access to per-server information) as self.server.  Since a
	separate instance is created for each request, the handle() method
	can define arbitrary other instance variariables.

	"""

	def __init__(self, request, client_address, server):
		self.request = request
		self.client_address = client_address
		self.server = server
		if not server.procHelper:
			self.procHelper = None
		else:
			self.procHelper = server.procHelper
		self.waited_conns = {}
		print "INIT BaseRequestHandler"
		#traceback.print_stack()
		try:
			self.setup()
			self.handle()
			self.finish()
		finally:
			sys.exc_traceback = None	# Help garbage collection

	def setup(self):
		pass

	def handle(self):
		pass

	def finish(self):
		pass

# The following two classes make it possible to use the same service
# class for stream or datagram servers.
# Each class sets up these instance variables:
# - rfile: a file object from which receives the request is read
# - wfile: a file object to which the reply is written
# When the handle() method returns, wfile is flushed properly


class StreamRequestHandler(BaseRequestHandler):

	"""Define self.rfile and self.wfile for stream sockets."""

	# Default buffer sizes for rfile, wfile.
	# We default rfile to buffered because otherwise it could be
	# really slow for large data (a getc() call per byte); we make
	# wfile unbuffered because (a) often after a write() we want to
	# read and we need to flush the line; (b) big writes to unbuffered
	# files are typically optimized by stdio even when big reads
	# aren't.
	rbufsize = -1
	wbufsize = 0

	def setup(self):
		self.connection = self.request
		self.rfile = self.connection.makefile('rb', self.rbufsize)
		self.wfile = self.connection.makefile('wb', self.wbufsize)

	def finish(self):
		if not self.wfile.closed:
			self.wfile.flush()
		self.wfile.close()
		self.rfile.close()
