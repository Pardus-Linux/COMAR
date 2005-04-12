#	Default TA Handlers.

# COMAR modules
import RPCData
import COMARValue

createpid = None
createttsid = None

class TA_TTSGEN:
	def __init__(self):
		pass
	def status(self):
		tts = createttsid(scope = "HOST")
		R = RPCData.RPCStruct()
		R.TTSID = "_TTSGEN_"
		R.makeRPCData("RESPONSE")
		R["status"]	= "RESULT"
		R["TTSID"]	= R.TTSID
		R["returnvalue"] = COMARValue.COMARRetVal(result = 0, value = COMARValue.string_create(tts))
		return R
	def create(self):
		return None
	def cancel(self):
		return None

HANDLERS = { "_TTSGEN_": TA_TTSGEN }
