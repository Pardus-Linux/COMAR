import sys, os, popen2, stat, select
from errno import *
# COMARValue.COMARRetVar( 'value':None, 'result':0 )
# Sample API File..
def	dummycheckPerms(perm, file):
	return 1
def	APICLASS():
	return "SYS"

_APICLASS  = "SYS"

checkPerms = dummycheckPerms
def isexecutable(file=""):
	print "isexecutable:", file,
	try:
		st = os.stat(file.split(" ")[0])
	except:
		print "FALSE (ERR_STAT)"
		st = None
	if st:
		if st[0] & stat.S_IEXEC:
			print "TRUE"
			return 1
		print "FALSE (NOEXEC)"
	return 0
	
class APICALLS:
	def __init__(self, IAPI, COMARValue):
		self.siglist = { "SIGHUP":1, "SIGINT":2, "SIGQUIT":3, "SIGILL":4,
						"SIGTRAP":5, "SIGABRT":6, "SIGBUS":7, "SIGFPE":8,
						"SIGKILL":9, "SIGUSR1":10, "SIGSEGV":11, "SIGUSR2":12,
						"SIGPIPE":13, "SIGALRM":14, "SIGTERM":15, "SIGCHLD":17,
						"SIGCONT":18, "SIGSTOP":19, "SIGTSTP":20, "SIGTTIN":21,
						"SIGTTOU":22, "SIGURG":23, "SIGXCPU":24, "SIGXFSZ":25,
						"SIGVTALRM":26, "SIGPROF":27, "SIGWINCH":28, "SIGIO":29,
						"SIGPWR":30, "SIGSYS":31, "SIGRTMIN":32 }
		self.IAPI = IAPI
		self.cv = COMARValue
		self.objHandlers = {}
		
	def	GetFuncTable(self):
		return { 'sendsignal':self.sendsignal,
				 'kill':self.sendsignal,
				 'grep_startif':self.grepstartif,
				 'grep_first':self.grepfirst,
				 'grepfirst':self.grepfirst,
				 'createdaemon': self.daemonize,
				 'execute':self.execute,
				 'capture':self.capture_stdout,
				 'getfile':self.get_file,
				 'putfile':self.put_file,
				 'removefile' : self.rmfile}
				 
	def execute(self, _name = "", prms = {}, checkPerms=dummycheckPerms, callerInfo=None):
		keylist = prms.keys()
		prg = ""			
		for prm in keylist:
			if prm == "program" or prm == "exec":
				prg = prms[prm].data.value
			if checkPerms(perm = "PROCESS_EXEC", file=prg) and isexecutable(prg):
				self.exec_stdout(prg)
				return self.cv.COMARRetVal( value=st, result=0 )
				
			return self.cv.COMARRetVal(value=None, result = EBADF)
			
	def rmfile(self, _name = "", prms = {}, checkPerms=dummycheckPerms, callerInfo=None):
		keylist = prms.keys()
		prg = ""			
		for prm in keylist:
			if prm == "file":
				prg = prms[prm].data.value
			
		if prg != "" and checkPerms(perm = "FILE_DEL", file=prg):
			try:
				os.unlink(prg)
			except:
				pass
			return self.cv.COMARRetVal( value=None, result=0 )
			
		return self.cv.COMARRetVal(value=None, result = EBADF)
			
	def put_file(self, _name = "", prms = {}, checkPerms=dummycheckPerms, callerInfo=None):
		keylist = prms.keys()
		file = None
		buffer = None
		for prm in keylist:			
			if prm == "file":
				file = prms[prm].data.value		
			elif prm == "buffer":
				buffer = prms[prm].data.value		
		if file and buffer:
			if checkPerms(perm = "FILE_WRITE", file=file):
				fd = open(file, "w")
				wb = fd.write(buffer)
				fd.close()
				return self.cv.COMARRetVal( value= self.cv.numeric_create(0), result=0 )				
			return self.cv.COMARRetVal( value=self.cv.numeric_create(0), result=EPERM )
			
	def get_file(self, _name = "", prms = {}, checkPerms=dummycheckPerms, callerInfo=None):
		keylist = prms.keys()
		file = None
		buffer = None		
		for prm in keylist:			
			if prm == "file":
				file = prms[prm].data.value		
				break
		if file:
			if checkPerms(perm = "FILE_READ", file=file):
				fd = open(file, "r")
				wb = fd.readlines()
				fd.close()				
				ret = self.cv.string_create("".join(wb))				
				return self.cv.COMARRetVal( value = ret, result=0 )
			return self.cv.COMARRetVal( value=self.cv.numeric_create(0), result=EPERM )
	
	def capture_stdout(self, _name = "", prms = {}, checkPerms=dummycheckPerms, callerInfo=None):
		keylist = prms.keys()
		prg = ""
		startwith = None
		for prm in keylist:
			filter = 1
			if prm == "program" or prm == "exec":
				prg = prms[prm].data.value
			elif prm == "ignoreblanklines":
				filter = prms[prm].toBoolean()
			elif prm == "startwith":
				startwith = prms[prm].data.value
			
		if checkPerms(perm = "PROCESS_EXEC", file=prg):
			if isexecutable(prg):
				lines = self.exec_stdout(prg)
				ret = self.cv.array_create()
				x = 0
				for line in lines:			
					if len(line) > 1 or filter:
						if startwith == None:
							self.cv.array_additem(array=ret, key="%04d" % (x), arrValue=self.cv.string_create(line))
							x += 1
						else:
							if line[:len(startwith)] == startwith:
								self.cv.array_additem(array=ret, key="%04d" % (x), arrValue=self.cv.string_create(line))
								x += 1
				#print "capture stdout:", self.cv.dump_value_xml(ret)
				if x == 0:
					ret = self.cv.string_create("")
				return self.cv.COMARRetVal( value=ret, result=0 )
				
			return self.cv.COMARRetVal(value=self.cv.string_create(""), result = EBADF)			
		return self.cv.COMARRetVal(value=self.cv.string_create(""), result = EPERM)
		
	def daemonize(self, _name = "", prms = {}, checkPerms=dummycheckPerms, callerInfo=None):
		keylist = prms.keys()
		prg = ""
		for prm in keylist:
			if prm == "program" or prm == "exec":
				prg = prms[prm].data.value

		if checkPerms(perm = "PROCESS_EXEC", file=prg):
			if isexecutable(prg):
				pid = os.fork()
				if pid:
					return self.cv.COMARRetVal( value=pid, result=0 )
				else:
					os.setsid()
					args = prg.split(" ")
					exe = args[0][:]
					args.pop(0)
					print "Daemonize:", exe, args
					os.execv(exe, args)
					os._exit(0) # Not reach..

				return self.cv.COMARRetVal( value=0, result=EBADF )
		return self.cv.COMARRetVal( value=0, result=EPERM )

	def exec_stdout(self, prg = ""):
		pipe = popen2.Popen3(prg)
		lines = []
		while pipe.poll() == -1:
			select.select([],[],[], 0.1)
			lines.extend(pipe.fromchild.readlines())
		lines.extend(pipe.fromchild.readlines())
		pipe.wait()
		lines.extend(pipe.fromchild.readlines())
		return lines
		
	def grepfirst(self, _name = "", prms = {}, checkPerms=dummycheckPerms, callerInfo=None):
		keylist = prms.keys()
		prg = ""
		search_pattern = ""
		end_pattern = []
		begin_pattern = []
		for prm in keylist:
			if prm == "program" or prm == "exec":
				prg = prms[prm].data.value
			elif prm == "pattern":
				search_pattern = prms[prm].data.value
		results = []
		line_ok = 0
		logical_line = ""

		if checkPerms(perm = "PROCESS_EXEC", file=prg):
			try:
				lines = self.exec_stdout(prg)
				for line in lines:
					#print "grep_startif:", line, search_pattern
					if line != "":
						if line.find(search_pattern) != -1:
							results.append(line)
							break
			except:
				pass

		if len(results) > 0:
			self.cv.string_create(results[0])
			return self.cv.COMARRetVal(0, self.cv.string_create(results[0]))
		return self.cv.COMARRetVal( value=self.cv.string_create(""), result=0 )

	def grepstartif(self, _name = "", prms = {}, checkPerms=dummycheckPerms, callerInfo=None):
		"""
		Run 'exec' and capture stdout. But, only
		started with 'pattern' and ended with 'end_pattern'
		lines captured.
		Return a COMAR Array
		prms:
			pattern  		= Start pattern for captured lines
			exec, program 	= Application for look stdout..
			end_pattern 	= Optional line end_pattern.
							  If a captured line ended with this pattern
							  next line merged with this line..
			begin_pattern	= Optional line begin pattern.
							  If a captured line started with this pattern
							  previous line merged with this line..
		"""

		keylist = prms.keys()
		prg = []
		search_pattern = []
		end_pattern = []
		begin_pattern = []
		for prm in keylist:
			if prm == "program" or prm == "exec":
				prg.append(prms[prm].data.value)
			elif prm == "pattern":
				search_pattern.append(prms[prm].data.value)
			elif prm == "end_pattern":
				end_pattern.append(prms[prm].data.value)
			elif prm == "begin_pattern":
				begin_pattern.append(prms[prm].data.value)

		results = []
		line_ok = 0
		logical_line = ""
		for exe in prg:
			if checkPerms(perm = "PROCESS_EXEC", file=exe):
				pipe = popen2.Popen3(exe)
				while 1:
					line = pipe.fromchild.readline()					
					if line == "":
						break

					if len(logical_line) > 0:
						if line_ok:
							logical_line += line
							for e in end_pattern:
								if line[-len(e):] == e:
									line_ok = 1
									break
						else:
							for b in begin_pattern:
								if line[:len(b)] == b:
									logical_line += line
									for e in end_pattern:
										if line[-len(e):] == e:
											line_ok = 1
											break
									break
					else:
						line_ok = 0
						for i in search_pattern:
							if line[:len(i)] == i:
								if logical_line != "":
									results.append(logical_line)
								logical_line = line
								for e in end_pattern:
									if line[-len(e):] == e:
										line_ok = 1
										break
				if logical_line != "":
					results.append(logical_line)

		if len(results) > 0:
			ret = self.cv.array_create()
			key = 0
			for res in results:
				key += 1				
				self.cv.array_additem(array = ret, key = key.__str__(),  arrValue = self.cv.string_create(res))
			return self.cv.COMARRetVal( value = ret, result=0 )

		return self.cv.COMARRetVal(arrValue = self.cv.string_create(""), result=0 )


	def sendsignal(self, _name = "", prms = {}, checkPerms=dummycheckPerms, callerInfo=None):
		""" prms:
		 signalname = SIG* POSIX signal name.
		 signal = POSIX Signal number.
		 program = process executable name. Only full Path allowed. repeatable..
		"""
		keylist = prms.keys()		
		sig = self.siglist["SIGHUP"]
		prg = []
		for prm in keylist:
			if prm == "program":
				prg.append(prms[i].data.value)
			elif prm == "signalname":
				if self.siglist.has_key(prms[i].data.value):
					sig = self.siglist[prms[i].data.value]
			elif prm == "signal":
				isig = int(prms[i])
				if isig > 1 and isig < 33:
					sig = isig
	
		dirent = listdir("/proc")
		for path in dirent:
			if path.isdigit():
				file = readlink("/proc/" + path + "/exe")
				for i in prg:
					if file == i:
						if checkPerms(perm = "PROCESS_CONTROL", file=file):
							kill(int(path), sig)

		return self.cv.COMARRetVal( value=None, result=0 )

class	API_FILEIO:
	def __init__(self, IAPI, COMARValue):
		self.IAPI = IAPI
		self.objHandlers = { "CAPI:SYS:FILEIO": (None, self.fileObjHandler) }

	def	GetFuncTable(self):
		return { 'openfile':None,
				  'execute':None,
				  'makedir':None }
	def fileObjHandler(self, objClass = "", objid = "", callType = "", callName = "", prms = {},callerInfo = None):
		pass

API_MODS = [ APICALLS, API_FILEIO ]
