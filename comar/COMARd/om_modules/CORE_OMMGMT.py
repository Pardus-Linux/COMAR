#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  Event Subsystem.
#

from errno import *
class objModelMgr:
	def __init__(self, dbHelper = None, CV = None, OMMGR = None):
		self.dbHelper	= dbHelper
		self.CV			= CV
		self.methodVtbl = {	"om.addNode":self.om_addNode,
							"om.addNodeScript":self.om_addNodeScript,
							"om.delNodeScript":self.om_delNodeScript,
							"om.addNodePreProc":self.om_addNodePreProc,
							"om.addNodePostProc":self.om_addNodePostProc,
							"om.setNodeProfile":self.om_setNodeProfile,
							"om.delNodePreProc":self.om_delNodePreProc,
							"om.delNodePostProc":self.om_delNodePostProc,
							"om.getACLChain":self.om_getACLChain,
							"om.insertACL":self.om_insertACL,
							"om.delACL":self.om_delACL,
							"om.setNodeProfile":self.om_setNodeProfile }
		self.propVtbl	= {	"om.Policy":(self.om_Policy_get, self.om_Policy_set) }
		self.objDriver	= { "OM:CORE:EMBED:OM": (None, self.om_objDriver) }
		self.OMMGR		= OMMGR

	def om_addnewInstance(self, prms = {}, callerInfo = None):
		if callerInfo.caller == "UI":
			return
		if not prms.has_key("index"):
			return
		index 		= self.CV.getPrmVal(prms, "index")
		node 		= callerInfo.caller
		key			= callerInfo.caller
		#print "Add New OM Code:", node, AppID, fileName, lang, code.__str__()[0:25], self.OMMGR
		name = self.OMMGR.parseNodeName(node)
		OMH = self.OMMGR.OMHandler(name[0])
		#print "OM Manger Module Entry:", node, "->", OMH
		#print "Call Real NS Manager Code:", 
		return OMH.addNewInstance(node = name[1], index = index[1], key="")

	def om_delInstance(self, prms = {}, callerInfo = None):
		pass
	def om_addNode(self, prms = {}, callerInfo = None): #parent="node", name="nodeName"
		"""Belirtilen parent noduna ("NS:node") bağlı yeni bir node oluşturur. Bu işlem gerçekleşirse, yeni node'un "NS:Node" formatındaki adını geri döndürür. Aksi durumda, hiç bir şey döndürmez. Node ekleme işlemi, tipik ACL vs. checking mekanizması dışında, sadece bu özelliği kabul eden namespace'lere uygulanabilir."""
		pass
	def om_addNodeScript(self, prms = {}, callerInfo = None): #node="NS:node", AppID="", fileName="", code="code", language="CSL"
		"""Belirtilen düğüme, kodu yeni bir nesne olarak ekler. fileName, dosya adı olarak kullanıma uygun, path kısmı bulunmayan, kodun tanıtıcı değeri olarak kullanılan bir isimdir. AppID, sistem tarafından oluşturulan uygulama tanımlayıcısıdır. Bir uygulama içinden aynı fileName'a sahip iki (or more) script herhangi bir NS'ye eklenemez. Bu giriş için, bilhassa UI üzerinden yapılan çağrılarda AppID kullanılmaz. Bunun yerine yapılan çağrının realm değeri kullanılır. Paket yöneticileri, yeni bir script eklemek üzere, bu çağrıyı doğrudan kullanmamalıdırlar. Bunun yerine COMAR-OM üzerinde paket yönetimi için ayrılan girdilerden bu çağrıyı yapmalıdırlar."""
		#print "AddNodeScript Called with:", prms
		if	(not prms.has_key("code")) or (not prms.has_key("node")) or (not prms.has_key("fileName")) or (not prms.has_key("AppID")):
			return
		code 		= self.CV.getPrmVal(prms, "code")
		AppID 		= self.CV.getPrmVal(prms, "AppID")
		fileName 	= self.CV.getPrmVal(prms, "fileName")
		lang 		= self.CV.getPrmVal(prms, "language")
		if lang == None:
			lang = "CSL"
		else:
			lang = lang[1]
		node		= self.CV.getPrmVal(prms, "node")
		#print "Add New OM Code:", node, AppID, fileName, lang, code.__str__()[0:25], self.OMMGR
		name = self.OMMGR.parseNodeName(node[1])
		OMH = self.OMMGR.OMHandler(name[0])
		#print "OM Manger Module Entry:", node, "->", OMH
		#print "Call Real NS Manager Code:", 
		return OMH.addNodeScript(node = name[1], IID = AppID[1], code = code[1], fileName = fileName[1], scriptType = lang)

	def om_delNodeScript(self, prms = {}, callerInfo = None): #node="NS:node", AppID="", fileName=""
		"""Belirtilen düğümdeki nesneyi kaldırır."""
		pass
	def om_addNodePreProc(self, prms = {}, callerInfo = None):
		#node="NS:node", code="", language="CSL")
		#node="NS:node", object=obj, method="methodName")
		"""Belirtilen düğüme yeni bir preprocessor kodu ekler."""
		pass
	def om_addNodePostProc(self, prms = {}, callerInfo = None):
		"""Belirtilen düğüme yeni bir postprocessor kodu ekler."""
		pass
#addNodePreProc/addNodePostProc çağrıları, başarılı oldukları sürece scriptId string döndürürler.
		pass
	def om_delNodePreProc(self, prms = {}, callerInfo = None): #node="NS:node", scriptid="scriptId")
		pass
	def om_delNodePostProc(self, prms = {}, callerInfo = None): #node="NS:node", scriptid="scriptId")
		"""Belirtilen scriptId'yi düğümün pre/post zincirinden kaldırır."""
		pass
	def om_getACLChain(self, prms = {}, callerInfo = None): #node="NS:node")
		"""Belirtilen düğüme ait ACL'lerin bir listesini COMARArray olarak döndürür. Array'ın her bir elemanı priority sıralamasını index olarak kullanan aşağıdaki array'den oluşur:
	quick	= "Y"/"N"
	invert	= "Y"/"N"
	mode	= "allow"/"deny"
	look	= ACL türü.
	value	= Karşılaştırılacak değer"""
		pass
	def om_Policy_get(self, index = None, callerInfo = None):
		pass
	def om_Policy_set(self, index = None, callerInfo = None, value = None):
		pass
	def om_insertACL(self, prms = {}, callerInfo = None):
		#node="NS:node", position=0, quick="N", invert="N", mode="allow|deny", look="ACL", value="deger")
		"""Düğüme yeni bir ACL ekler.
		position	: Tanımlanmamışsa, yeni ACL zincirin en sonuna eklenir. Diğer değerler için, yeni ACL belirtilen pozisyona eklenir ve bu poizsyondaki ACL ve ötesindekiler bir ileriye kaydırılır."""
		pass
	def om_delACL(self, prms = {}, callerInfo = None):
		"""Belirtilen pozisyondaki ACL'i siler."""
		pass

	def om_setNodeProfile(self, prms = {}, callerInfo = None):
		"""Belirtilen pozisyondaki ACL'i siler."""
		pass
	def om_objDriver(self, objClass = "", objid = "", callType = "", callName = "", prms = {},callerInfo = None):
		pass
