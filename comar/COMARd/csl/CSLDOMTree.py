import	types
import 	copy

class 	NSObject:
		def	__init__(self, name, runobject):
			pass

class	DOMObject:
		def __init__(self, _name):			
			self.ACL = []
			self.PRE = []
			self.POST = []
			self.next = None
			self.prev = None
			self.child = None
			self.parent = None
			self.objectstack = []
			self.name = _name
			
		def AddTrigger(self, Location = "OnCall", Hook = ""):
			""" AddTrigger install a container hook. 
				Location: OnCall - Trigged in container entry point,
				          OnReturn - Trigged on container exti point
				Hook: Hook point identifier			
			"""
			if Hook == None:
				return None				
			if Location.upper == "ONCALL":
				self.PRE.append(Hook)				
			if Location.upper == "ONRETURN":
				self.POST.append(Hook)				

		def AddACL(self, ACLMethod = "CONTAINER", ACLCondition = "__ALL__", ACLAction = "ALLOW"):
			if ACLAction == "ALLOW":
				__x = 1
			else:
				__x = 0
				
			__a = { "Method":ACLMethod, \
					"Condition":ACLCondition, \
					"Action": __x }
			self.ACL.append(copy.deepcopy(__a))
			del __a
			
		def	DelACL(self, ACLMethod = "CONTAINER", ACLCondition = "__GENERIC__"):
			for __i in self.ACL:
				if __i["Method"] == ACLMethod:
					if __i["Condition"] == ACLCondition:
						self.ACL.remove(self.ACL.index(__i))
						
		def CheckACL(self, ACLMethod = "CONTAINER", ACLCondition = "__GENERIC__"):
			for __i in self.ACL:
				if __i["Method"] == ACLMethod:
					if __i["Condition"] == ACLCondition:
						return __i["Action"]
			return 0;
			
		def BindObject(self, object = 0):
			try:
				__a = self.objectstack.index(object)
			except:
				self.objectstack.append(object)
		
		def SetChild(self, object):
			if type(object) == type(self):
				if self.child == None and object.parent == None:
					self.child = object
					object.parent = self
					return object
					
		def SetNext(self, object):
			if type(object) == type(self):
				if self.next == None and object.prev == None:
					self.next = object
					object.prev = self
					return object
			
		def WalkNext(self):
			if self.next == None:
				return None
			return self.next
			
		def WalkChild(self):
			if self.child == None:
				return None
			return self.child
				
		def AddObject(self, code):
			self.objectstack.append(code)
			
		def GetObject(self):
			return self.objectstack
