CSLValue = None
CSLAPI_NAME = "variable"
debug = None

moddir = dir()

def getFuncTable():
	vtbl = {}
	cls = API()
	for i in dir(cls):
		if i[:4] == "csl_":
			vtbl[i[4:]] = getattr(cls, i)
	return vtbl
	
class API:	
	def csl_arrayhasvalue(self, prms):
		ret = ""
		if prms.has_key("array") and prms.has_key("value"):
			arr = prms["array"].value
			val = prms["value"].value
			#print "hasvalue:", prms, arr, val
			if type(arr) != type({}):
				return CSLValue("numeric", 0)
			for i in arr.keys():
				if arr[i].value == val:
					return CSLValue("numeric", 1)
			return CSLValue("numeric", 0)
	def csl_arrayhaskey(self, prms):
		ret = ""
		if prms.has_key("array") and prms.has_key("key"):
			arr = prms["array"].value
			val = prms["key"].value					
			if type(arr) != type({}):
				return CSLValue("numeric", 0)
			#print "haskey:", prms, arr.keys(), val
			if val in arr.keys():
				return CSLValue("numeric", 1)
			return CSLValue("numeric", 0)
	def csl_typeof(prms):
		var = None
		if prms.has_key("var"):
			var = prms["var"]
		if prms.has_key("variable"):
			var = prms["variable"]
		if var:
			return CSLValue("string", var.type)
		else:
			return CSLValue("string", "NULL")
