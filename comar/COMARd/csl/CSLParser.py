import copy, cPickle, traceback, os
import CSLUtils

class CSLParse:
	# Features:
	# if..elif..else 		: SUCCESS
	# for(start_op; cond; repeat_op): SUCCESS
	# identifier = expression	: SUCCESS
	# Expression parsing		: SUCCESS
	# Array determination		: SUCCESS
	# property/method/functions	: SUCCESS
	# persistence			: N/A
	# alias				: SUCCESS
	# while, break, pass, abort	: SUCCESS


	def	__init__(self, code=None, file=None):
		self.CSLOperators = [ "*", "/", "+", "-", "%", "^", "==", ">=", "<=", "<", ">", "!=", "&&", "||" ]
		self.CSLIdCharsFree = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
		self.CSLIdCharsStart = self.CSLIdCharsFree + "$"
		self.CSLIdCharsEnd = self.CSLIdCharsFree + "0123456789"
		self.CSLIdCharsMid = self.CSLIdCharsEnd + ":."

		self.CSLIdCharsNumeric = "0123456789."

		self.CSLIdCharsCondID = self.CSLIdCharsFree + self.CSLIdCharsNumeric +\
								"".join(self.CSLOperators) + "[]()$"

		self.CSLCond = [ "==", ">=", "<=", "<", ">", "!=", "&&", "||" ]

		self.block_cmds = { "function":self.CSLBlkCmd_Func, "method": self.CSLBlkCmd_Method, "property": self.CSLBlkCmd_Prop }
		self.cond_cmds = [ "if", "else", "elif", "while" ]
		self.oneshot_cmds = [ "break", "pass", "abort" ]

		self.CSLrec = [0, 0]
		self.__propmode = 0

		self.ATbl = {} # Arrays.
		self.FTbl = {} # Function calls
		self.ITbl = {} # Variables.
		self.NTbl = {} # Numbers.
		self.OTbl = {} # Operations (*, /, +..)
		self.QTbl = {} # Strings..
		self.Profiles = {}
		self.Globals = {}
		self.GloPersist = {}

		self.IDStack = []

		self.nest = 0
		if file != None:
			f = open(file)
			code = "".join(f.readlines())
			#print "FILE:", code

		__code = self.CSLPreProcess(code)
		print "Preparsed Code:", __code
		a = CSLTreeNode(None, "ROOT", None)
		#print 'NEW CODE:', __code
		self.__tree = self.CSLParseCode(__code, a)
		self.tree = a
		self.nest = 0
		#self.CSLPrintTree(a)
		#buf = cPickle.dumps(a)
		#print "Pickle Buffer:", buf
		#nr = cPickle.loads(buf)
		#print "NEWTREE:"
		self.CSLPrintTree(self.tree)

	def CSLNodeFix(this, a):
		if a.type == None:
			if a.next != None:
				a = a.next
			else:
				a = a.child
		return a

	def CSLPrintTree(this, a, file = None, pre=""):
		f = file
		x = 0
		while a != None: # and x < 18:
			if file:
				f.write(pre + "    " * this.nest)
				f.write ("%s %s %s" % (a.type, "->", a.data))
			else:
				print "    " * this.nest,
				print a.type, "->", a.data,
			if a.child != None:
				if file:
					f.write(" GO CHILD\n")
				else:
					print "GO CHILD"

				this.nest += 1
				this.CSLPrintTree(a.child, file, pre)
				this.nest -= 1
				a = a.next
			elif a.next != None:
				if file:
					f.write(" GO NEXT\n")
				else:
					print "GO NEXT"
				a = a.next
			else:
				if file:
					f.write(" END\n")
				else:
					print "END.."
				a=None
			x += 1

	def CSLParseGlobals(this, code):
		linenum = 0
		__st = 0
		__stop = len(code)
		__lc = 0

		while __st < __stop:

			_l = this.CSLParseGetLine(code, __st)
			if _l == None:
				return
			__lp = 1
			__lc += 1
			__st = (this.CSLSkipSpaces(_l.data, 0) + _l.ptr) - 1
			while __lp:		# Process current line
				# _l is current line
				__ll = ""
				__rr = ""
				__id = this.CSLParseCheckIdRight(_l.data)

				if __id != None:
					__rr = _l.data[len(__id):]
					__rr = __rr[this.CSLSkipSpaces(__rr, 0):]
					if __id == "profile":
						__x = this.CSLParseCheckIdRight(__rr)
						if __x == None:
							print "Invalid Profile - missing identifier", __x
							return None

						print "Profile:", __x

						prfId = __x
						__rr = __rr[len(__x):]
						__rr = __rr[this.CSLSkipSpaces(__rr, 0):]

						ov = this.CSLParseCheckIdRight(__rr)
						print "Over:", ov, __rr
						if ov != "over":
							print "Invalid Profile Command - Format: profile <id> over <Variable>;", _l.data
							return None

						__rr = __rr[len(ov):]
						__rr = __rr[this.CSLSkipSpaces(__rr, 0):]


						__n = __rr.split(",")
						__a = []

						for __i in __n:
							__i = __i.strip()
							__j = this.CSLParseCheckIdRight(__i)
							if __j != __i:
								print "Invalid Profile - invalid profile name:", __id, __rr
								return None
							__a.append(__j)
						print "Profile", __x ,"over:", __a
						this.Profiles[__x] = __a
						del __a
						del __j
						#print "ALIAS: ", __x, "->", __n
						__st = _l.ptr
						__lp = 0
						pass
					elif __id == "global":
						__x = this.CSLParseCheckIdRight(__rr)
						__n = __rr.split(",")
						for __i in __n:
							__i = __i.strip()
							__j = this.CSLParseCheckIdRight(__i)
							if __j != __i:
								print "Invalid Global Variables - invalid name:", __id, __rr
								return None
							this.Globals[__j] = None
							print "Global Variable:", __j

						del __j
						#print "PERSISTENT: ", __x, "->", __n
						__st = _l.ptr
						__lp = 0
						pass

					elif __id == "instance":
						__x = this.CSLParseCheckIdRight(__rr)
						if __x == "over":
							prfId = __x
							__rr = __rr[len(__x):]
							__rr = __rr[this.CSLSkipSpaces(__rr, 0):]

							ov = this.CSLParseCheckIdRight(__rr)

							__rr = __rr[len(ov):]
							__rr = __rr[this.CSLSkipSpaces(__rr, 0):]
							print "Instance Over:", ov, __rr
						else:
							ov = None
						__n = __rr.split(",")
						for __i in __n:
							__i = __i.strip()
							__j = this.CSLParseCheckIdRight(__i)
							if __j != __i:
								print "Invalid Global Instance Variables - invalid name:", __id, __rr
								return None
							this.GloPersist[__j] = { 'profile': ov, 'value':None }
							print "Global Instance:", __j, this.GloPersist[__j]

						del __j
						#print "INSTANCE: ", __x, "->", __n
						__st = _l.ptr
						__lp = 0
						pass

				else:	# get identifier from line, but no valid identifier
					print "Invalid Identifier:", _l.data, __id, __ll, __rr
					__lp = 0
					os._exit(1)
					break

			#this.CSLPrintTree(__retnode)
			if __st< __stop:
				if code[__st] == ";":
					__st += 1
				__st = this.CSLSkipSpaces(code, __st)

			if (__st < __stop):
				pass
			else:
				break

	def CSLBlkCmd_Func(this, code, root, codedata):
		return this.CSLBlkCmd_FuncWP(code, root, codedata, "deffunc")

	def CSLBlkCmd_Method(this, code, root, codedata):
		return this.CSLBlkCmd_FuncWP(code, root, codedata, "defmethod")

	def CSLBlkCmd_FuncWP(this, code, root, codedata, defid):

		__popen = -1
		__pos = 0
		__p = None
		# print "TDATA:", code
		for __x in code:
			if __x == '(':
				__popen = __pos
			elif __x == ')':
				break
			__pos += 1

		if __popen != -1 :
			# __pos = ")" position - 1
			# __popen = "(" position
			if __pos < __popen + 1:
				print "Missing expression in parenthesis: ", code
				return None

			# check Left Hand list..
			# only "(", "<operator>", "<operator> identifier" accepted..


			# check Right Hand List..
			# only ")" "<operator>" accepted..
			__rl = code[__pos+1:]
			__data = code[__popen+1:__pos]

			__ll = code[:__popen]
			#print "FUNC DEF: LL:", __ll, "RL:", __rl, "DATA:", __data
			if __ll != "":
				__id = this.CSLParseCheckId(__ll)
				if __id != "":
					__ll = __ll[:len(__ll) - len(__id)]
					__p = __data.split(",")
					#print " -> ", __p
					__po = {}
					for __i in __p:
						# print "CHK P:", __i
						__x = __i.find("=")
						if __i == "":
							#print "Invalid parameter - no parameter"
							#return None
							#print "Func with no parameter!"
							pass
						elif __x == -1:
							print "Invalid parameter - use var=value notation"
							return None

						__pl = __i[:__x]
						__pr = __i[__x + 1:]
						# print "PRMSET: PL: ", __pl, " PR:", __pr

						__po[__pl] = this.CSLParseExpression(__pr)

					__p = CSLTreeNode(None, defid, { "name":__id, 'prmlist': __po })

					__n = this.CSLParseCode(codedata, None)

					if __n == None:
						return None

					if __n.type == None:
						__n = __n.next
					if __p and __n:
						__p.child = __n
						__n.parent = __p

				else:
					__sub = this.CSLParseExpression(__data)
			else:
				__sub  = this.CSLParseExpression(__data)
			return __p

	def CSLBlkCmd_Prop(this, id, root, codedata):
		code = id
		__ret = None
		while 1:
			__popen = -1
			__pos = 0
			__inp = 0
			__last = -1
			__nest = 0
			__ln = 0
			__lpf = -1

			for __x in code:

				if __x == "[":
					__nest += 1
					__lp = __pos

				elif __x == "]":
					if __nest > __ln:
						__ln = __nest
						__last = __pos
						__lpf = __lp
					__nest -= 1

				__pos += 1

			__popen = __lpf
			__pos = __last

			if __popen != -1 :
				# __pos = "]" position - 1
				# __popen = "[" position

				if __pos <= __popen + 1:
					print "Missing expression in parameter: ", code
					return None

				__ll = code[:__popen]


				if __ll == "": return None

				# end of __ll is exist..
				if __ll != "":
					__id = this.CSLParseCheckId(__ll)
				if __id == None: return None

				# __id = identifier. Seek indexes:

				__ll = __ll[:len(__ll) - len(__id)]

				__rl = code[__popen - 1:]

				__l = 0
				__i = -1
				__p = []

				for __x in code[__popen:]:

					if __x == "[":
						__i += 1
						__p.append("")
						__l = 0
					elif __x == "]":
						__l = 1
					else:
						if __l:
							break
						__p[__i] += __x
					__rl = __rl[1:]

				if __rl != "" and __ll != "":
					if __rl[0] == "]" and __ll[-1] != "[":
						__rl = __rl[1:]
				elif __rl != "" and __ll == "":
					if __rl[0] == "]":
						__rl = __rl[1:]

				if len(__p) > 1:
					print "A Property can't be have multiple indexes"
					return None

				__i = __p[0]
				__x = __i.find("=")
				if __i == "":
					print "Invalid Property call: no parameter!"
					return None
				elif __x == -1:
					print "Invalid parameter - use var=value notation"
					return None

				__pl = __i[:__x]
				__pr = __i[__x + 1:]

				__pr = this.CSLParseExpression(__pr)

				__p = CSLTreeNode(None, "defprop", { "name":__id, 'prm': __pl, 'default':__pr })

				this.__propmode = 1
				__n = this.CSLParseCode(codedata, None)
				this.__propmode = 0
				if __n == None:
					return None

				if __n.type == None:
					__n = __n.next

				__p.child = __n
				__n.parent = __p

				__ret = __p
				break
			else:					# No more parenthesis
				__p = CSLTreeNode(None, "defprop", { "name":id.strip(), 'prm':'', 'default':'' })
				this.__propmode = 1
				__n = this.CSLParseCode(codedata, None)
				this.__propmode = 0

				if __n == None:
					return None
				if __n.type == None:
					if __n.next != None:
						__n = __n.next
					else:
						__n = __n.child
				if __p and __n:
					__p.child = __n
					__n.parent = __p

					__ret = __p
				break

		return __ret

	pinst = 0
	def CSLCleanTabs(this, s):
		n = ""
		f = s.split("\n")
		for i in f:
			n = n + f.strip() + "\n"
		return n
	def CSLParseCode(this, code, root = None):
		linenum = 0
		__st = 0
		__stop = len(code)
		__lc = 0
		if root == None:
			root = CSLTreeNode(None, None, None);

		__retnode = root
		this.pinst += 1
		pinstance = this.pinst
		inwhile = 0
		#print "PARSER:",this.pinst,"\n",  code
		#print traceback.print_stack(None,5)
		while __st < __stop:
			if root.type != None and root.next != None:
				root = root.next

			# get a line..
			#print root.type, "->", root.data
			linenum += 1
			_l = this.CSLParseGetLine(code, __st)
			#print "CODE :",this.pinst, _l.data, root.type, root.data
			#print "Code Line: %d -> '%s'" % (_l.ptr, _l.data)
			if 0:
				f = open("parserout", "a")
				f.write("\nPROCESS LINE: %s/%s %s" % (pinstance, linenum, _l.data))
				f.close()
			if _l == None:
				return
			__lp = 1
			__lc += 1
			__st = (this.CSLSkipSpaces(_l.data, 0) + _l.ptr) - 1
			while __lp:		# Process current line
				# _l is current line
				__ll = ""
				__rr = ""
				__id = this.CSLParseCheckIdRight(_l.data)
				#print "Code Line: %d -> '%s' %s in %s" % (_l.ptr, _l.data, __id, code[__st:__st+100])
				#this.CSLPrintTree(__retnode)
				if __id != None:
					__rr = _l.data[len(__id):]
					__rr = __rr[this.CSLSkipSpaces(__rr, 0):]
					if __id in this.cond_cmds:
						# a conditional command found..
						if root.type == "ROOT" or this.__propmode:
							print __id, "Can't be defined here!"
							return None
						this.IDStack.append(__id)
						#print "BCMD PREV:", code[__st:__st+50]
						rs = this.CSLParseWithCond(__rr, root)
						__p = rs[0]
						#__st += rs[1]
						#print "BCMD AFTER:", code[__st:__st+50]
						if __p.type == None:
							__p = __p.next
						root.next = __p
						__p.prev = root
						__p.parent = root.parent
						root = __p
						__x = this.IDStack.pop()
						__st = this.CSLSkipSpaces(code, __st)
						if __st < len(code) and code[__st] == "{":		# a codeblock!
							#print "Found Code Block over:", code
							__sub = CSLUtils.findlast(code[__st:], "", "{", "}")
							if __sub == -1:
								#print "Canceled BCMD", __x
								return None
							__sc = code[__st+1:__st+__sub-1]
							__st += __sub
							__n = this.CSLParseCode(__sc, None)
							if __n:
								root.child = __n.next
								__n.parent = root
							#print "BCMD BLOCK RESULT OF ", __x
							#this.CSLPrintTree(root)
						break

					elif __id == "globals":
						if root.type != "ROOT" or this.__propmode:
							print __id, "Can't be defined here!"
							return None

						if __st < len(code) and code[__st] == "{":	# a codeblock!
							__sub = CSLUtils.findlast(code[__st:], "", "{", "}")
							if __sub == -1:
								return None
							__sc = code[__st+1:__st+__sub-1]
							__st += __sub

						print "Globals:", __sc
						this.CSLParseGlobals(__sc)
						print __rr, "CODE ST:", _l.data, code[__st:__st + 100]

						break

					elif __id == "for":
						if root.type == "ROOT" or this.__propmode:
							print __id, "Can't be defined here!"
							return None

						this.IDStack.append(__id)
						#DBG# print "found cond. cmd:", __id, "with RR:", __rr

						__p = this.CSLParseCmdFor(__rr, root)

						if __p.type == None: __p = __p.next
						root.next = __p
						__p.prev = root
						__p.parent = root.parent

						root = __p
						__x = this.IDStack.pop()

						if __p == None:
							return

						if __st < len(code) and code[__st] == "{":	# a codeblock!
							__sub = CSLUtils.findlast(code[__st:], "", "{", "}")

							if __sub == -1:
								return None
							__sc = code[__st+1:__st+__sub-1]

							__st += __sub
							__n = this.CSLParseCode(__sc, None)
							__p.child = __n.next
							__n.parent = root
							# on last node, node can't point vs. etc..
						break

					elif __id == "foreach":
						if root.type == "ROOT" or this.__propmode:
							print __id, "Can't be defined here!"
							return None

						this.IDStack.append(__id)
						#DBG# print "found foreach:", __id, "with RR:", __rr

						__p = this.CSLParseCmdForeach(__rr, root)

						if __p.type == None: __p = __p.next
						root.next = __p
						__p.prev = root
						__p.parent = root.parent

						root = __p
						__x = this.IDStack.pop()

						if __st < len(code) and code[__st] == "{":		# a codeblock!
							__sub = CSLUtils.findlast(code[__st:], "", "{", "}")

							if __sub == -1:
								return None
							__sc = code[__st+1:__st+__sub-1]
							__st += __sub
							__n = this.CSLParseCode(__sc, None)
							__p.child = __n.next
							__n.parent = root
							# on last node, node can't point vs. etc..

						else:
							# get next code and insert it child node..
							pass

						break

					elif this.block_cmds.has_key(__id) :

						if ((root.type != "ROOT" and (root.parent != None and root.parent.type != "ROOT")) or this.__propmode):
							print __id, "Can't be defined here!"
							return None

						if __st < len(code) and code[__st] == "{":		# a codeblock!

							## Check its type:
							__sub = CSLUtils.findlast(code[__st:], "", "{", "}")

							if __sub == -1:
								return None
							this.IDStack.append(__id)
							__sc = code[__st+1:__st+__sub-1]

							__st += __sub

							__n = this.block_cmds[__id](__rr, root, __sc)

							if __n == None :
								return None
							elif __n.type == None:
								__n = __n.next
							if root.type == "ROOT":
								root.child = __n
								__n.parent = root

							else:
								root.next = __n
								__n.prev = root

							root = __n

						else:
							# get next code and insert it child node..
							this.IDStack.append(__id)

							__p = this.CSLParseCode(__rr, root)

							if __p.type == None: __p = __p.next
							if __p == None:
								return

							root.next = __p
							__p.prev = root
							__p.parent = root.parent
							root = __p
							__x = this.IDStack.pop()

						break
					elif __id == "get" or __id == "set":
						if this.__propmode == 0:
							print __id, "Can't be use here!"
							return None
						__p = root

						while __p != None:
							if __p.type != None and __p.type == __id:
								print __id, " already defined!"
								this.CSLPrintTree(__retnode)
								break
							__p = __p.prev

						if __p != None:
							return None

						if __st < len(code) and code[__st] == "{":		# a codeblock!
							__sub = CSLUtils.findlast(code[__st:], "", "{", "}")

							if __sub == -1:
								return None
							this.IDStack.append(__id)
							__sc = code[__st+1:__st+__sub-1]
							__st += __sub
							this.__propmode = 0
							__n = this.CSLParseCode(__sc, None)
							this.__propmode = 1
							if __n == None :
								return None

							elif __n.type == None:
								if __n.next != None:
									__n = __n.next
								else:
									__n = __n.child

							__p = CSLTreeNode(None, __id, None)
							if __p and __n:
								__p.child = __n
								__n.parent = __p
								root.next = __p
								__p.prev = root
								root = __p
							__x = this.IDStack.pop()
						else:
							# get next code and insert it child node..
							this.IDStack.append(__id)
							#*
							this.__propmode = 0
							__n = this.CSLParseCode(__rr, None)
							this.__propmode = 1
							if __n == None :
								return None
							elif __n.type == None:
								if __n.next != None:
									__n = __n.next
								else:
									__n = __n.child

							__p = CSLTreeNode(None, __id, None)

							__p.child = __n
							__n.parent = __p
							root.next = __p
							__p.prev = root
							root = __p
							__x = this.IDStack.pop()
							#*

						break
					elif __id in this.oneshot_cmds :
						# oneshot command..
						if root.type == "ROOT" or this.__propmode:
							print __id, "Can't be defined here!"
							return None

						if __rr != "":
							print "'%s' cannot be accept a parameter. (%s)" % (__id, __rr)
							return None

						__p = CSLTreeNode(None, __id, None)
						if __p.type == None: __p = __p.next
						root.next = __p
						__p.prev = root
						__p.parent = root.parent
						root = __p
						__st = _l.ptr
						__lp = 0
					elif __id == "alias":
						__x = this.CSLParseCheckIdRight(__rr)
						if __x == None:
							print "Invalid Alias - missing identifier"
							return None
						__p = CSLTreeNode(None, __id, None)
						if __p.type == None: __p = __p.next

						__n = __rr[len(__x):].split(",")
						__a = []
						for __i in __n:
							__i = __i.strip()
							__j = this.CSLParseCheckIdRight(__i)
							if __j != __i:
								print "Invalid Alias - invalid alias name:", __id, __rr
								return None
							__a.append(__j)

						__p.data = { 'identifier':__x, 'aliases': copy.deepcopy(__a) }
						del __a
						del __j
						#print "ALIAS: ", __x, "->", __n
						root.next = __p
						__p.prev = root
						__p.parent = root.parent
						root = __p
						__st = _l.ptr
						__lp = 0
						pass
					elif __id == "persistent":
						__x = this.CSLParseCheckIdRight(__rr)
						__n = __rr.split(",")
						__a = []
						for __i in __n:
							__i = __i.strip()
							__j = this.CSLParseCheckIdRight(__i)
							if __j != __i:
								print "Invalid Persistent Variables - invalid name:", __id, __rr
								return None
							__a.append(__j)
						__p = CSLTreeNode(None, __id, None)
						__p.data = { 'variables': copy.deepcopy(__a) }

						del __a
						del __j
						#print "PERSISTENT: ", __x, "->", __n
						root.next = __p
						__p.prev = root
						__p.parent = root.parent
						root = __p
						__st = _l.ptr
						__lp = 0
						pass

					elif __id == "instance":
						__x = this.CSLParseCheckIdRight(__rr)
						__n = __rr.split(",")
						__a = []
						for __i in __n:
							__i = __i.strip()
							__j = this.CSLParseCheckIdRight(__i)
							if __j != __i:
								print "Invalid Instance Variables - invalid name:", __id, __rr
								return None
							__a.append(__j)
						__p = CSLTreeNode(None, __id, None)
						__p.data = { 'variables': copy.deepcopy(__a) }

						del __a
						del __j
						#print "INSTANCE: ", __x, "->", __n
						root.next = __p
						__p.prev = root
						__p.parent = root.parent
						root = __p
						__st = _l.ptr
						__lp = 0
						pass

					elif __id == "makeinstance":
						__n = __rr.split(",")
						__a = []
						for __i in __n:
							__i = __i.strip()
							__j = this.CSLParseCheckIdRight(__i)
							if __j != __i:
								print "Invalid Instance Variables - invalid name:", __id, __rr
								return None
							__a.append(__j)
						__p = CSLTreeNode(None, __id, None)
						if len(__a) == 3:
							__p.data = { "objname": __a[0], "objid":__a[1], "autodestroy": __a[2] }
						elif len(__a) == 2:
							__p.data = { "objname": __a[0], "objid":__a[1], "autodestroy": "n" }
						else:
							print "Invalid makeinstance usage - invalid name:", __id, __rr
							return None

						del __a
						del __j
						#print "MAKE	INSTANCE: ", __id, "->", __n
						root.next = __p
						__p.prev = root
						__p.parent = root.parent
						root = __p
						__st = _l.ptr
						__lp = 0
						pass

					elif __id == "register":
						__i = __rr.strip()
						__j = this.CSLParseCheckIdRight(__i)
						if __j != __i:
							print "Invalid Register object - invalid name:", __id, __rr
							return None
						__p = CSLTreeNode(None, __id, None)
						__p.data = { "objname": __j }

						print "REGISTER: ", __id, "->", __j
						del __j
						del __i
						root.next = __p
						__p.prev = root
						__p.parent = root.parent
						root = __p
						__st = _l.ptr
						__lp = 0
						pass

					elif __id == "destroy":
						if __rr == "":
							__a = ['me']
						else:
							__n = __rr.split(",")
							__a = []
							for __i in __n:
								__i = __i.strip()
								__j = this.CSLParseCheckIdRight(__i)
								if __j != __i:
									print "Invalid Destroy Command - invalid name:", __id, __rr
									return None
								__a.append(__j)
						__p = CSLTreeNode(None, __id, None)
						__p.data = { 'instances': copy.deepcopy(__a) }

						del __a
						del __j
						#print "DESTROY INSTANCE: ", __x, "->", __n
						root.next = __p
						__p.prev = root
						__p.parent = root.parent
						root = __p
						__st = _l.ptr
						__lp = 0
						pass

					else:
						# possible ID = EXPRESSION call ? (Not cond.cmd)
						#print "LET Entry.."
						if root.type == "ROOT" or this.__propmode:
							print __id, __rr, "Can't be defined here!"
							return None

						while (1):
							if root.type == None:
								if root.prev:
									root = root.prev
							if __rr[0] == "=":
								# We found a ID = EXPRESSION
								#print "LET: '%s' = '%s'" % (__id, __rr)
								__exp = this.CSLParseExpression(__rr[1:])

								# ***********************
								# We return information as "id = exp" form
								# but, we want must transform this:
								# LETI $In, exp
								__lp = 0
								__n = CSLTreeNode(root, "LET", { 'id':__id, 'exp': __exp }) #self, parent, type, nodedata

								root.next = __n
								__n.parent = root.parent
								__n.prev = root
								root = __n
								break
							elif "*/+-%^".find(__rr[0]) != -1 and len(__rr) > 1:
								if __rr[1] == "=":
									__exp = this.CSLParseExpression(__rr[2:])
									__op = __rr[:1]
									#print "LET: '%s' = '%s''%s''%s'" % (__id, __id, __op[0], __exp)
									__n = CSLTreeNode(root, __op, { 'src':__id, 'dst': __exp }) #self, parent, type, nodedata
									root.next = __n
									__n.prev = root
									__n.parent = root.parent
									root = __n
								__lp = 0
								break
							elif __rr[0] == "(":	# a method call?
								__data = __rr[1:CSLUtils.findlast(__rr, "", "(", ")")-1]
								__rr = __rr[len(__data)+2:]
								if __rr.strip() != "":
									print "Invalid chars at end-of-line ignored:", _l.data, __rr
								__p = __data.split(",")
								#print " -> ", __p
								__po = {}
								for __i in __p:
									# print "CHK P:", __i
									__x = __i.find("=")
									if __i == "":
										print "Invalid parameter - no parameter"
										return None
									elif __x == -1:
										print "Invalid parameter - use var=value notation"
										return None

									__pl = __i[:__x]
									__pr = __i[__x + 1:]
									# print "PRMSET: PL: ", __pl, " PR:", __pr

									__po[__pl] = this.CSLParseExpression(__pr)

								#print "METHOD: ", __id, "PRM = ", __po, "RR:", __rr
								__n = CSLTreeNode(root, "CALL", { "method": __id, "prm": __po }) #self, parent, type, nodedata
								root.next = __n
								__n.prev = root
								__n.parent = root.parent
								root = __n
								__lp = 0
								break
							elif __rr[0] == "[":
								# ***********************
								# We return information as "id[prm] = exp" form
								# but, we want must transform this:
								# LETA $An, exp
								__rr = __id+__rr
								__sub = this.CSLMakeArrayId(__rr)

								if __sub == None:
									print "Unknown Array ID:", _l.data, "RR:", __rr
									return
								_l.data = __sub
								_l.ptr = 0
								#print "AID SUB:", __sub, "RR:", __rr
								break

							else:
								print "Syntax Error: LLine: %d " % (__lc), _l.data
								__lp = 0
								break

				else:	# get identifier from line, but no valid identifier
					print "Invalid Identifier:", _l.data, __id, __ll, __rr
					__lp = 0
					os._exit(1)
					break

			#this.CSLPrintTree(__retnode)
			if 0:
				f = open("parserout", "a")
				f.write(" PROCESS LINE RESULT: %s/%s %s " % (pinstance, linenum, _l.data))
				this.CSLPrintTree(root, f, "L %s/%s" % (pinstance, linenum))
				this.CSLPrintTree(__retnode, f, "P%s/%s " % (pinstance, linenum))
				f.close()

			if __st< __stop:
				if code[__st] == ";":
					__st += 1
				__st = this.CSLSkipSpaces(code, __st)

			if (__st < __stop):

				pass
			else:
				break
			if 0:
				if __retnode.type == None and __retnode.child != None:
					__retnode = __retnode.child
				f = open("parserout", "a")
				f.write("PARSER RETURN: %s %s %s\nPARSE RESULT: %s\n" % (pinstance, "FOR CODE:", code, pinstance))
				this.CSLPrintTree(__retnode, f)
				f.close()
		return __retnode

	def CSLParseCmdForeach(this, code, node):
		# for each syntax:
		# foreach (array; keyid; instanceid; valueid)
		# foreach (keyid[:instanceid] = valueid in arrayid)
		# keyid and instanceid cannot be a object..
		__c = code[this.CSLSkipSpaces(code, 0):]
		# if a code block defined:

		if len(__c) == 0:
			print "Bad Value (cmd:foreach):", code
			return None


		if __c[0] == "(":		# Valid character ! Bingo !
			__x = CSLUtils.findlast(__c, "", "(", ")")
			__data = __c[1:__x-1]
			__rr = __c[__x:]

			#print "data: '%s' rr: '%s'" % (__data, __rr)
			if __data.find(' in ') != -1 and __data.find('=') != -1:
				# var:instance = value in array format
				arrayid = this.CSLParseCheckId(__data)
				__data = __data[:len(__data) - len(arrayid)].strip()
				#print "ARR:", arrayid, '-', __data
				__x = this.CSLParseCheckId(__data)
				__data = __data[:len(__data) - len(__x)].strip()
				#print "IN:", __x, '-', __data
				if __x == 'in':
					valueid = this.CSLParseCheckId(__data)
					__data = __data[:len(__data) - len(valueid)].strip()
					#print "VAL:", valueid, '-', __data
					__x = this.CSLParseCheckIdRight(__data)
					__data = __data[len(__x):].strip()
					#print 'X:', __x, '-', __data
					if __data != '=':
						print "Please read CSL Syntax manual for 'foreach' and don't repeat this line:", __c
						return None
					keyid = __x
					instanceid = ''
					for __i in range(len(__x)-1, -1, -1):
						if __x[__i] == ":":
							keyid = __x[:__i]
							instanceid = __x[__i+1:]
							break
					__n = CSLTreeNode(None, this.IDStack[-1], { 'array': arrayid, 'instance': instanceid, 'keyid': keyid, "value": valueid } )
					#print __n.data
					if __rr != "":
						__x = this.CSLParseCode(__rr, None)
						__x = __x.next
						__n.child = __x
						__x.parent = __n
						if (__n.type) == None: __n = __n.next
					return __n

				else:
					print "Please read CSL Syntax manual for 'foreach' and don't repeat this line:", __c
					return None

			else:
				# foreach (array; keyid; instanceid; valueid) format
				arrayid = this.CSLParseCheckId(__data)

				if arrayid == None:
					print "Invalid Array identifier on 'foreach':", __c
					return None

				__data = __data[:len(__data)-len(arrayid)].strip()



				if this.CSLParseCheckId(__data) != "in":
					print "Syntax Error, really, see next line and find an 'in' on valid position:\n", __c, "\nif you can see it, send a bug report to CSL Team.."
					return None

				__data = __data[:len(__data)-2].strip()

				valueid = this.CSLParseCheckId(__data)

				if arrayid == None:
					print "Invalid Value identifier on 'foreach':", __c
					return None

				__data = __data[:len(__data)-len(arrayid)].strip()

				if __data[-1] != "=":
					print "Please read CSL Syntax manual for 'foreach' and don't repeat this line:", __c
					return None

				__data = __data[:len(__data)-1]

				for __i in range(len(__data)-1, -1, -1):
					if __data[__i] == ":":
						keyid = __data[:__i]
						instanceid = __data[__i+1:]
						break

				if keyid == None:
					keyid = __data
					instanceid = None

				__n = CSLTreeNode(None, this.IDStack[-1], { 'array': arrayid, 'instance': instanceid, 'keyid': keyid, "value": valueid } )

				if __rr != "":
					__x = this.CSLParseCode(__rr, None)
					__x = __x.next
					__n.child = __x
					__x.parent = __n
					if (__n.type) == None: __n = __n.next
				return __n
		else:					# A Problem ! Syntax Error..
			print "Bad syntax on 'foreach' statement:", __c

	def CSLParseCmdFor(this, code, node):
		__c = code[this.CSLSkipSpaces(code, 0):]
		# if a code block defined:

		if len(__c) == 0:
			print "Bad Value (cmd:for):", code
			return None


		if __c[0] == "(":		# Valid character ! Bingo !
			__x = CSLUtils.findlast(__c, "", "(", ")")
			__data = __c[1:__x-1]
			__rr = __c[__x:]

			_l = this.CSLParseGetLine(__data, 0)
			__start = None
			__cond = None
			__oper = None
			if _l != None:
				__x = _l.ptr
				__start = this.CSLNodeFix(this.CSLParseCode(_l.data, None))
				_l = this.CSLParseGetLine(__data, __x)
				if _l != None:
					__cond = this.CSLParseExpression(_l.data)
					__x =  _l.ptr # (this.CSLSkipSpace_l.data, __x) +
					_l = this.CSLParseGetLine(__data, __x)
				if _l != None:
					__oper =this.CSLNodeFix(this.CSLParseCode(_l.data, None))
					__x =  _l.ptr
					_l = this.CSLParseGetLine(__data, __x)
				if _l != None:
					print "Invalid 'for' syntax:", __c, __l.data
					return None

			__n = CSLTreeNode(None, this.IDStack[-1], { 'start': __start, 'cond':__cond, 'oper': __oper } )

			if __rr != "":
				__x = this.CSLParseCode(__rr, None)
				__x = __x.next
				__n.child = __x
				__x.parent = __n
				if (__n.type) == None: __n = __n.next

			return __n

		else:					# A Problem ! Syntax Error..
			print "Bad syntax on statement:", __c

	def CSLParseWithCond(this, code, node):
		# generic handler for statements:
		# while, else, elif, if
		fst = this.CSLSkipSpaces(code, 0)
		__c = code[fst:]
		# if a code block defined:
		if this.IDStack[-1] == "else":
			__n = CSLTreeNode(None, this.IDStack[-1], { 'cond':None })
			if len(__c) != 0:
				__p = this.CSLParseCode(code, None).next
				__n.child = __p
				__p.parent = __n

			return __n, fst

		if len(__c) == 0:
			print "Bad Value:", code
			return None


		if __c[0] == "(":		# Valid character ! Bingo !
			__x = CSLUtils.findlast(__c, "", "(", ")")
			__data = __c[1:__x-1]
			__rr = __c[__x:]
			skip = fst + __x #len(__data)
			__cond = this.CSLParseExpression(__data)
			#print "Conditional Block:",  this.IDStack[-1]
			__n = CSLTreeNode(None, this.IDStack[-1], { 'cond':__cond })
			if __rr != "":
				skip += len(__rr)
				__x = this.CSLParseCode(__rr, None)
				if __x.type == None:
					__x = __x.next
				__n.child = __x
				__x.parent = __n
				if (__n.type) == None: __n = __n.next

			return __n, skip

		else:					# A Problem ! Syntax Error..
			print "Bad syntax on statement:", __c



	def CSLParseGetCond(this, code):
		__ll = ""
		__rr = ""
		__parserun = 1
		self = this
		for __i in this.CSLCond:
			while (__parserun):

				__pos = code.find(__i)
				# print "CIN: ", __i
				if __pos == -1:
					#print ""
					break

				__ll = code[:__pos]
				__op = __i
				__rr = code[__pos+ len(__i):]
				__lid = None
				__rid = None
				# print "CO:%s CODE:%s LL:'%s' RR:'%s'" % (__i, code, __ll, __rr)

				__f = 0
				for __x in range(len(__ll) - 1, -1, -1):					
					if __ll[__x] != " ": break
					
				for __x in range(__x, -1, -1):					
					# print "FIND: %d '%s' " % (__x, __ll[__x]),
					# print self.CSLIdCharsCondID.find( __ll[__x] )
					if (self.CSLIdCharsCondID.find( __ll[__x] )) == -1:
						__lid = __ll[__x+1:]
						__ll = __ll[:__x + 1]
						__f = 1
						break
				
				if __f == 0:
					__lid = __ll
					__ll = ""

				__f = 0
				
				for __x in range(0, len(__rr) - 1):
					#print "RR EXP: %d -> '%s'" % (__x, __rr[__x])
					if __rr[__x] != " ": 
						#print "NEW RR: ", __rr[__x:]
						break

				for __x in range(__x, len(__rr) - 1):
					if self.CSLIdCharsCondID.find( __rr[__x] ) == -1:
						__rid = __rr[:__x]
						__rr = __rr[__x:]
						__f = 1
						break

				if __f == 0:
					__rid = __rr
					__rr = ""

				#print "COND: LL: '%s' LID: '%s' OP: '%s' RID: '%s' RR: '%s'" % \
				#		(__ll, __lid, __op, __rid, __rr)

				if __lid == None or __rid == None:	# a problem ?
					print "A Problem !", code
					__parserun = 0
					break

				__lid = this.CSLParseExpression(__lid)
				__rid = this.CSLParseExpression(__rid)

				this.CSLrec[0] += 1

				__hnd = "$C" + str(this.CSLrec[0])
				this.CTbl[__hnd] = { "op": __op, "dst": __lid, "src": __rid }

				code = __ll + __hnd + __rr
				#print "ECODE:", code

			if __parserun == 0: break


	def CSLParseGetLine(this, code, start):
		__line = ""
		if start >= len(code): return None
		start = CSLUtils.skipSpaces(code, start)
		__ps = 0
		for __i in code[start:]:
			if __i == ";" and __ps == 0:
				break
			elif __i == '\n':
				if __line != "" and __line[-1] == "\\":
					__line[-1] = __i

			elif __i == "{":
				break
			else:
				if __i == "(": __ps += 1
				if __i == ")": __ps -= 1
				__line += __i
			start += 1
		__ret = CSLParserRet()
		__ret.ptr = start + 1
		__ret.data = __line
		return __ret

	def CSLSkipSpaces(this, code, start):
		for __i in code[start:]:
			if " \n\t\r".find(__i) == -1: break
			start += 1
		return start


	def CSLParseCheckId(this, code):
		""" return identifier from "blabla identifier"
			reverse find (end to first (R..L)) and return
			identifier from code..
		"""
		__ll = code
		__ops = "=[(" + "".join(this.CSLOperators)
		
		if __ll != "":
			#if 	__ll[-1] in __ops:
			#print "CPCID:", __ll	
			if this.CSLIdCharsEnd.find(__ll[-1]) != -1:				
				# print  "CAN BE AN ID:", __ll
				__ls = 0
				__l = ""
				
				for __i in range(len(__ll) - 1 , -1, -1): # $@$ ,-1, -> ,0,
					__l = __ll[__i]
					if this.CSLIdCharsMid.find(__l) == -1:
						if this.CSLIdCharsStart.find(__l) == -1:
							__ls = __i
							break						
							
				if __l != "":
					if __ops.find(__l) != -1 or __l == ' ':
						__ls += 1
						
				__id = __ll[__ls:]
				#print "FOUND ID: '%s' " % __id
				if this.CSLIdCharsStart.find(__id[0]) == -1 or __ls < 0:
					#if __id[0] in "0123456789":
					#	rv = this.CSLParseGetNumLeft(code)
					#	if rv != None:
					#		return rv
					print "Syntax Error: (1) Invalid character '%s' on begin of identifier:" % __id[0], __ll, "on", code
					#traceback.print_stack()
					return None
				for __i in __id[1:len(__id) - 2]:
					if this.CSLIdCharsMid.find(__i) == -1:
						print "Syntax Error: Invalid characters:", __ll, "on", code
						return None
			else:				
				rv = this.CSLParseGetNumLeft(code)
				if rv != None:
					return None
				print "Syntax Error: (2) Invalid character '%s' on end of identifier:" % __ll[-1], __ll, "on", code
				#traceback.print_stack()
				return None

		if __id[-1] == " ":
			__id = __id[:len(__id) - 2]
		return __id

	def CSLParseCheckIdRight(this, code):
		""" return identifier from "identifer blabla"
			find (start to end (L..R)) and return
			identifier from code..
		"""

		__ll = code
		__ops = "=[(" + "".join(this.CSLOperators)
		#print "SEEK RID FOR:", code
		__id = None
		if __ll != "":
			if this.CSLIdCharsStart.find(__ll[0]) != -1:
				# print  "CAN BE AN ID:", __ll
				__ls = len(__ll) - 1
				__l = ""
				__id = __ll[0]
				for __i in range(1, __ls + 1): # $@$ ,-1, -> ,0,
					__l = __ll[__i]
					#print "I: ", __i, " L:" , __l
					if this.CSLIdCharsMid.find(__l) == -1:
						if this.CSLIdCharsEnd.find(__l) == -1:
							#print "BREAK RID"
							break

					__id += __l

				# print "FOUND RID: '%s' " % __id

				if this.CSLIdCharsStart.find(__id[0]) == -1 or __ls < 0:
					# print "Syntax Error: Invalid character '%s' on begin of identifier:" % __id[0], __ll, "on hum", code
					traceback.print_stack()	
					return None

				if this.CSLIdCharsEnd.find(__id[-1]) == -1:
						# print "Syntax Error: Invalid character '%s' on end of identifier:" % __id[-1], __ll, "on", code
					return None

				for __i in __id[1:len(__id) - 2]:
					if this.CSLIdCharsMid.find(__i) == -1:
						# print "Syntax Error: Invalid characters:", __ll, "on", code
						return None

			else:
				# print "Syntax Error: Invalid character '%s' on end of identifier:" % __ll[-1], __ll, "on", code
				return None

		if __id != None and __id != "" and __id[-1] == " ":
			__id = __id[:len(__id) - 1]
		return __id

	def CSLMakeArrayId(this, code):

		while 1:
			__popen = -1
			__pos = 0
			__inp = 0
			__last = -1
			__nest = 0
			__ln = 0
			__lpf = -1
			
			for __x in code:

				if __x == "[":
					__nest += 1
					__lp = __pos
					# print "NEST-UP:", __nest, __pos
				elif __x == "]":
					if __nest > __ln:
						__ln = __nest				
						__last = __pos
						__lpf = __lp
					__nest -= 1	
					# print "NEST:", __nest, __pos
				__pos += 1
			# print "RES: %d LAST: %d LPF: %d " % (__ln, __lpf, __last)
			__popen = __lpf 
			__pos = __last

			if __popen != -1 :
				# __pos = "]" position - 1
				# __popen = "[" position

				if __pos <= __popen + 1:
					print "Missing expression in parameter: ", code
					return None
	
				__ll = code[:__popen]
							
				# print "LL: ", __ll
				if __ll == "": return None
				
				# end of __ll is exist..
				if __ll != "":
					__id = this.CSLParseCheckId(__ll)
					
				if __id == None: return None
				
				# __id = identifier. Seek indexes:
				
				# print "INDEXES: ", code[__popen:]
				
				__ll = __ll[:len(__ll) - len(__id)]			

				__rl = code[__popen - 1:]
				
				__l = 0
				__i = -1
				__p = []
				
				for __x in code[__popen:]:
					
					if __x == "[":
						__i += 1
						__p.append("")
						__l = 0
					elif __x == "]":
						__l = 1	
					else:
						if __l:						
							break
						__p[__i] += __x
					__rl = __rl[1:]
	
				# print "RL COMP: RL:'%s' LL:'%s' ->" % (__rl, __ll),
				if __rl != "" and __ll != "":
					if __rl[0] == "]" and __ll[-1] != "[":
						__rl = __rl[1:]
				elif __rl != "" and __ll == "":
					if __rl[0] == "]":
						__rl = __rl[1:]

				# print "RL:'%s' LL:'%s'" % (__rl, __ll)


				#print "IDENTIFIER -> '%s' PRM: %s " % (__id, __p), "LEFT:",  __ll, "RIGHT:", __rl, "=",

				#__sub = CSLGetValue(__id, __p)

				this.CSLrec[0] += 1
				for __i in range(0, len(__p)):
					__p[__i] = this.CSLParseExpression(__p[__i])
					#print "P PRC:", __p[__i]

				__sub = '$A' + str(this.CSLrec[0])

				this.ATbl[__sub] = { "id": __id, "prmlist": __p }

				this.CSLrec[1] = len(__rl)

				code = __ll +  __sub + __rl
				#print code
			else:					# No more parenthesis
				#__data = CSLParseOper(
				break
		return code


	def	CSLParseExpression(this, code):

		# first pass, search and execute [index]
		code = this.CSLMakeArrayId(code)

		# second pass, search and process function calls.
		# a function call, typically formed:
		# identifier(param=value, param=value)

		# third pass, search and execute parenthesis.

		while 1:
			__popen = -1
			__pos = 0
			#print "PEXP TDATA:", code
			for __x in code:
				if __x == '(':
					__popen = __pos
				elif __x == ')':
					break
				__pos += 1

			if __popen != -1 :
				# __pos = ")" position - 1
				# __popen = "(" position
				if __pos < __popen + 1:
					print "Missing expression in parenthesis: ", code
					return None

				# check Left Hand list..
				# only "(", "<operator>", "<operator> identifier" accepted..

				# check Right Hand List..
				# only ")" "<operator>" accepted..
				__rl = code[__pos+1:]
				__data = code[__popen+1:__pos]

				__ll = code[:__popen]
				
				if __ll != "":
					#print "Call vaziyeti: ", __ll
					__id = this.CSLParseCheckId(__ll)
					#print "Return vaziyeti: ", __ll
					if __id != "" and __id != None:
						#print "FUNC:", __id, "PRMS:", __data,
						__ll = __ll[:len(__ll) - len(__id)]

						# parse func parameters..
						# a(b=c(fin=l))
						__p = __data.split(",")
						#print " -> ", __p
						__po = {}
						for __i in __p:
							# print "CHK P:", __i
							__x = __i.find("=")
							if __i == "":
								#print "Warning ! No parameter:", code
								pass
							elif __x == -1:
								print "Invalid parameter - use var=value notation"
								#traceback.print_stack()
								return None
							else:
								__pl = __i[:__x]
								__pr = __i[__x + 1:]
								# print "PRMSET: PL: ", __pl, " PR:", __pr
								__po[__pl] = this.CSLParseExpression(__pr)

						#print "FUNC: ", __id, "LAST PO = ", __po
						this.CSLrec[0] += 1
						__data = "$F" + str(this.CSLrec[0])
						this.FTbl[__data] = { "id": __id, "prmlist": __po }
						__sub = __data
					else:
						#print "() Datasi:", __data
						__sub = this.CSLParseExpression(__data)
				else:
					__sub  = this.CSLParseExpression(__data)
				# end of __ll is exist..				
				code = __ll + __sub + __rl
				#print "EXP New code: -> ", code
			else:					# No more parenthesis

				# at this point only '$' treeid's, numerics and identifiers
				# allowed...
				#print "NMP:", code

				__parserun = 1
				for __i in this.CSLOperators:
					while (__parserun):
						#print "O:%s CODE:%s " % (__i, code),
						__pos = code.find(__i)

						if __pos == -1:
							#print ""
							break

						__ll = code[:__pos]
						__op = __i
						__rr = code[__pos+len(__i):]

						__id = this.CSLParseCheckId(__ll)
						__num = None
						if __id == None:	# a problem ?
							__num = this.CSLParseGetNumLeft(__ll)

						if __id == None and __num == None:
							__parserun = 0
							print "Invalid value/identifier: ", code
							break


						if __num != None: 	# a number
							__ll = __ll[:len(__ll)-len(__num)]

						else:
							__ll = __ll[:len(__ll)-len(__id)]

						__iddst = __id
						__numdst = __num

						__id = this.CSLParseCheckIdRight(__rr)
						__num = None
						if __id == None:	# a problem ?
							__num = this.CSLParseGetNumRight(__rr)

						if __id == None and __num == None:
							__parserun = 0
							print "Invalid value/identifier: ", code
							break


						if __num != None: 	# a number
							__rr = __rr[len(__num):]

						else:
							__rr = __rr[len(__id):]

						this.CSLrec[0] += 1

						# Ready for tree..

						# __op = Operand / command
						# __iddst, __numdst = Destination
						# __id, __num = Source
						# form: operand dest, source


						if __iddst != None:
							__dst = "$I" + str(this.CSLrec[0])
							this.ITbl[__dst] = __iddst
						else:
							__dst = "$N" + str(this.CSLrec[0])
							this.NTbl[__dst] = __numdst

						this.CSLrec[0] += 1

						if __id != None:
							__src = "$I" + str(this.CSLrec[0])
							this.ITbl[__src] = __id
						else:
							__src = "$N" + str(this.CSLrec[0])
							this.NTbl[__src] = __num

						this.CSLrec[0] += 1

						__hnd = "$O" + str(this.CSLrec[0])
						this.OTbl[__hnd] = { "op": __op, "dst": __dst, "src": __src }

						#print "OPER: LL: '%s' RR: '%s' LID:'%s' LNUM:'%s' OP: '%s' RID:'%s' RNUM:'%s'" % (__ll,  __rr, __iddst, __numdst,__op, __id, __num),

						code = __ll + __hnd + __rr
						#print code
					if __parserun == 0: break

				break
		#print "CPE CODE: '%s'" % code
		if code != '' and code[0] != "$":
			code = code.strip()
			if this.CSLParseGetNumLeft(code) == code: # a number
				__dst = "$N" + str(this.CSLrec[0])
				this.NTbl[__dst] = code
				#print "ADD NUMBER: [%s] = %s" % (__dst,code)
				code = __dst
				this.CSLrec[0] += 1
			elif this.CSLParseCheckId(code) == code : # a identifier
				__dst = "$I" + str(this.CSLrec[0])
				this.ITbl[__dst] = code
				code = __dst
				this.CSLrec[0] += 1

			else:									  # Typically syntax error event..
				print "Syntax error in expression:", code
				return None
		return code

	def CSLParseGetNumLeft(this, code):
		__ll = code
		__ops = "=[(" + "".join(this.CSLOperators)
		if __ll != "":
			if this.CSLIdCharsNumeric.find(__ll[-1]) != -1:
				# print  "CAN BE AN ID:", __ll
				__ls = 0
				__l = ""
				#print "SEEKP:", __ll
				for __i in range(len(__ll) - 1 , -1, -1):
					__l = __ll[__i]
					# print "SEEK: ", __i, "=", __l
					if this.CSLIdCharsNumeric.find(__l) == -1:
						#print "BREAK!"
						__ls = __i
						break						
					
				
				#print "SEEKL: ", __i, "=", __l

				if __l != "":					
					if __ops.find(__l) != -1:
						__ls += 1
						
				__id = __ll[__ls:]

				#print "FOUND Number: '%s' " % __id

				for __i in __id[1:len(__id) - 2]:
					if this.CSLIdCharsNumeric.find(__i) == -1:
						#print "Syntax Error: Invalid characters:", __ll, "on", code
						return None
			else:
				#print "Syntax Error: Invalid character '%s' on end of number:" % __ll[-1], __ll, "on", code
				return None
		return __id
	
	def CSLParseGetNumRight(this, code):
		__ll = code
		__ops = "=[(" + "".join(this.CSLOperators)
		if __ll != "":			
			if this.CSLIdCharsNumeric.find(__ll[0]) != -1:				
				# print  "CAN BE AN ID:", __ll
				__ls = len(__ll) - 1
				__l = ""
				#print "SEEKP:", __ll
				for __i in range(0 , __ls + 1):
					__l = __ll[__i]
					#print "SEEK: ", __i, "=", __l
					if this.CSLIdCharsNumeric.find(__l) == -1:
						#print "BREAK!"
						__ls = __i
						break						
					
				
				#print "SEEKL: ", __i, "=", __l
				
				if __l != "":					
					if __ops.find(__l) != -1:
						__ls -= 1

				__id = __ll[:__ls + 1]
				
				#print "FOUND Number: '%s' " % __id
				
				for __i in __id[1:len(__id) - 2]:
					if this.CSLIdCharsNumeric.find(__i) == -1:
						#print "Syntax Error: Invalid characters:", __ll, "on", code
						return None
			else:
				#print "Syntax Error: Invalid character '%s' on end of number:" % __ll[-1], __ll, "on", code
				return None
		return __id
	
	
	def	GetObject(NSRoot, findpath):
		__a = NSRoot
		__path = findpath
		__x = __path.find('[')
		if __x >= 0:
			__index = __path[__x + 1:]
			__call = __index[__index.find(']')+2:]
			__index = __index[:__index.find(']')]
			__path = __path[0:__x]
		else:
			__index = "_DEFAULT"
			__call = __path[__path.rfind(".")+1:]
			__path = __path[0:__path.rfind(".")-2]
		if '\'"'.find(__index[0]) != -1:	#is start with quote?
			__newindex = ""
			__quot = __index[0]
			__inquot = 0
			__esc = 0
			for __x in range(1, len(__index) - 1):
				if __esc == 1:
					__newindex += __index[__x]
					__esc = 0
				else:
					if __index[__x] == __quot:
						__inquot = (__inquot + 1) % 2
						break
					else:
						if __index[__x] == '\\':
							__esc = 1
						else:
							__newindex += __index[__x]
			# end of for
			__index = __newindex
			del __newindex

		__x = 0
		__i = 0	
		while 1:		
			if __path[__x:].find(".") == -1:	#last occurrence						
				__p = __path[__x:]			
				while __a != None:
					if __a.name == __p:				
						break
					__a = __a.WalkNext()
				__ret = __a
				break
			else:
				__i = __path[__x:].find(".")
				__p = __path[__x:__i]
				while __a != None:
					if __a.name == __p:
						break
					__a = __a.WalkNext()
				if __a == None:
					__ret = __a
					break
				__a = __a.WalkChild()
				__x = __path[__x:].find(".") + 1
		if __ret != None:	# Container found at __ret
			return CSLNodeObject(__ret, __index, __call)

		return None


	def CSLPreProcess(this, code):
		__ret = ""
		__inquot = 0
		__esc = 0
		__quotestart = -1
		__qinx = 0
		__quot = ""
		__qo ="\"'"
		__qc = __qo
		remarkMode = 0
		for __i in code:
			if __esc:
				__esc = 0
				if __i == "t":
					__j = "\t"
				elif __i == "n":
					__j = "\n"
				elif __i == "\\":
					__j = "\\"
				else:
					__j = __i

				if __inquot:
					__quot += __j
				else:
					__ret += __j
			else:
				if remarkMode:
					if __i == "\n":
						remarkMode = 0
				else:
					if __i == "\\":
						__esc = 1
					elif __i == "#":
						if not __inquot:
							remarkMode = 1
					elif __qc.find(__i) != -1:

						if __inquot :		# Already in quote

							__ret += "$Q" + str(__qinx)

							this.QTbl["$Q" + str(__qinx)] = __quot
							__qinx += 1
							__inquot = 0
							__qc = __qo
							__quot = ""
						else:
							__inquot = 1
							__qc = __i
					else:
						if __inquot:
							__quot += __i
						else:
							__ret += __i

		__tmp = __ret

		__clr = [ "\n\n", " \n", "  ", " (", " )", " [", " ]", " ,", " !", " &", " =", " |"]
		for __qc in __clr:
			while __tmp.find(__qc) != -1:
				__i = __tmp.find(__qc)
				__tmp =  __tmp[:__i] + __tmp[__i+1:]

		__clr = ["( ", ") ", "[ ", "] ", ", ", "& ", "= ", "| " ]
		for __qc in __clr:
			while __tmp.find(__qc) != -1:
				__i = __tmp.find(__qc)
				__tmp =  __tmp[:__i+1] + __tmp[__i+2:]

		for __quot in this.CSLOperators:
			__qc = " " + __quot
			while __tmp.find(__qc) != -1:
				__i = __tmp.find(__qc)
				__tmp =  __tmp[:__i] + __tmp[__i+1:]

			__qc = __quot + " "
			while __tmp.find(__qc) != -1:
				__i = __tmp.find(__qc)
				__tmp =  __tmp[:__i+1] + __tmp[__i+2:]

		#------------------------
		# Create Numbers.
		l = __tmp
		numbers = "0123456789"
		validlefts = "\n */+-%^=<>&|[(;," + numbers
		validrights = "\n */+-%^=<>&|]);," + numbers
		fnd = 0
		cpos = 0
		xlen = len(l) - 1
		illegal = 0

		while cpos <= xlen:
			#print l[cpos]
			while l[cpos] == " " and cpos < xlen:
				cpos += 1
			if numbers.find(l[cpos]) != -1:
				x = cpos
				cs = l[l.rfind("\n", 0, x):l.find("\n", x)]
				if cpos == 0 or validlefts.find(l[cpos-1]) != -1:
					if cpos == xlen or validrights.find(l[cpos+1]) != -1 or l[cpos+1] == ".":
						x = cpos
						xstop = -2
						while x <= xlen:
							if numbers.find(l[x]) == -1:
								if l[x] == ".":
									cs = l[l.rfind("\n", 0, x):l.find("\n", x)]
									#print "Found: .", l[x-2], l[x-1], l[x], l[x+1], x, xlen, "'%s'" % cs.strip()
									if x == xlen or numbers.find(l[x+1]) == -1:
										print "Illegal dot:", x, xlen, l[x-1], l[x], l[x+1], cs.strip
										xstop = -1 #illegal
								else:
									if validrights.find(l[x]) == -1:
										xstop = -1 #illegal
									else:
										xstop = x
							x += 1
							if xstop != -2:
								if xstop == -1:
									return None
								num = l[cpos:xstop]
								ll = ""
								rr = ""
								if cpos > 0:
									ll = l[:cpos]
								if xstop < xlen:
									rr = l[xstop:]
								this.CSLrec[0] += 1
								_id = "$N%s" % this.CSLrec[0]
								n = len(_id)
								this.NTbl[_id] = num
								l = ll + _id + rr
								cpos += n
								xlen = len(l) - 1
								#print this.NTbl
								break
				else:
					x = cpos
					while x < xlen:
						if l[x] in numbers:
							x += 1
						else:
							break
					cpos = x

			cpos += 1
		#print "TMP:", l
		return l
		

class CSLNodeObject:
	def	__init__(self, DOMNode, IndexIdentifier = "", CallPoint = "default"):
		self.Node = copy.deepcopy(DOMNode)
		self.Identifier = copy.deepcopy(IndexIdentifier)
		self.CallItem = copy.deepcopy(CallPoint)


class CSLTreeNode:
	def	__init__(self, parent, type, nodedata):
		self.next = None
		self.prev = None
		self.child = None
		self.parent = None
		self.type = type
		self.data = nodedata
		self.logic = 0


class CSLParserRet:
	def __init__(self):
		self.direction = None
		self.data = None
		self.ptr = None
