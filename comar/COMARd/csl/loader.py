#!/usr/bin/python

import sys
sys.path.append('../COMARd')
mod = __import__('COMAR-API')
capi = mod.COMARCAPI()
ci = mod.callerInfoObject()
ci.OID	= 'objtest'
csl = __import__('CSLRunEnv')
hook = csl.COMARObjHook(instanceid = '234567', cAPI = capi, callerInfo = ci)
#hook.setSourceFromURL('file:///home/serdar/COMAR/csl/objtest.csl')
ret = hook.runMethod('check')
if ret.execResult == 0:
	print 'ret:', ret.returnValue
	print capi.COMARValue.dump_value_xml(ret.returnValue)
else:
	print 'Error returned:', ret.execResult


