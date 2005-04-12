def	findlast(str, quot_char = "\"'", blk_open = "{", blk_close ="}", start = 0, stop = 0):

	if stop == 0: 
		stop = len(str)		
		
	if quot_char == "" or quot_char == None: quot_char = "\"'"
	__inquot = 0
	__esc = 0
	__nest = 0
	__quot = quot_char
	__pos = start
	__last_pos = -1
	# print "PRM:",str[start:stop], start, stop, str 
	# print "PRM:", "01234567890123456789012345"
	# print "    ", "00000000001111111111222222"
	for __i in str[start:stop]:				
		if __quot.find(__i) != -1:		# quoute char?			
			if __esc:
				__esc = 0				
			else:
				__inquot = (__inquot + 1) % 2
				if __inquot:			# enter quote mode..
					__quot = __i
				else:
					__quot = quot_char
		else:			
			if __inquot == 0:			# not a quoted string?
				if __esc == 0:			# ESC CHAR not occurred?
					if __i == blk_open:	
						__nest += 1
					if __i == blk_close:						
						__nest -= 1						
						if __nest == 0:
							__last_pos = __pos + 1
							break
				else:
					__esc = 0
			else:
				if __i == "\\":
					# print "ESC MODE"
					__esc = 1
				
	
		__pos += 1	
	
	return __last_pos
	
def	skipSpaces(str, start = 0, stop = 0):

	if stop == 0: 
		stop = len(str)		
	
	__pos = 0
	__result = -1
	
	for __i in str[start:stop]:
		if " \n\t".find(__i) == -1:
			__result = start + __pos
			
			break
			
		__pos += 1
	
	return __result

class CSLIdentifier:
	def	__init__(self):
		self.start = 0
		self.stop  = 0
		self.id = ""
	
	
def getIdentifierPos(str, extrachars="", start=0, stop=0):

	if stop == 0: 
		stop = len(str)		

	__start = skipSpaces(str, start, stop)
	
	
	if __start == -1: return None
	
	
	__check = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_."
	__check += extrachars
	
	__pos = 0
	__result = -1
	
	for __i in str[__start:stop]:
		if __check.find(__i) == -1:
			__result = __pos + __start
			break
		__pos += 1
		
	if __pos+__start == stop:
		__result = stop
		
	__i = None
	
	if __result != -1:
		
		__i = CSLIdentifier()
		__i.start = __start
		__i.stop = __result			
		
	return __i
	
def getIdentifier(str, extrachars="", start=0, stop=0):
	
	
	
	__x = getIdentifierPos(str, extrachars, start, stop)	
	
	if (__x != None): 
		__x.id = str[__x.start:__x.stop]
	
	return __x
