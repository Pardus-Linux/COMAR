CSLValue = None
CSLAPI_NAME = "string"
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
	def csl_getbit(self, prms):
		ret = ""
		if prms.has_key("value") and prms.has_key("bit"):
			x = int(prms["value"].toNumeric())
			b = int(prms["bit"].toNumeric())
			print "GETBIT:", x, b, (2 ** b), x & (2 ** b)
			if x & (2 ** b):
				return CSLValue("numeric", 1)
			else:
				return CSLValue("numeric", 0)
		return CSLValue("numeric", 0)
	def csl_getnearvalue(self, prms):
		if prms.has_key("look") and prms.has_key("values"):
			s = prms["values"].value
			l = prms["look"].toNumeric()
			if s:
				yak = {}
				for i in s.keys():
					x = abs(int(i) - l)
					yak[x] = s[i]					
				m = yak.keys()
				m.sort()
				return yak[m[0]]	
		return CSLValue("numeric", 0)
	def csl_int(self, prms):
		if prms.has_key("string"):
			return CSLValue("numeric", int(prms["string"].toNumeric()))
