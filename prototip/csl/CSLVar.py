import	types
import 	copy
class	DOMObject:
		def __init__(self):			
			self.ACL = []
		def AddACL(self, ACLMethod = "CONTAINER", ACLCondition = "__ALL__", ACLAction = "ALLOW")
			__a = { "Method":ACLMethod, \
					"Condition":ACLCondition, \
					"Action":ACLAction }
			self.ACL.append(copy.deepcopy(__a))
			del __a
		def	DelACL(self, ACLMethod = "CONTAINER", ACLCondition = "__GENERIC__")
			for __i in self.ACL
				if (__i.
