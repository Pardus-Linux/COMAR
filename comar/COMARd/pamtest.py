#!/usr/bin/env python

import sys
import PAM
from getpass import getpass

def pam_conv(auth, query_list):

	resp = []

	for i in range(len(query_list)):
		query, type = query_list[i]
		if type == PAM.PAM_PROMPT_ECHO_ON:
			val = raw_input(query)
			resp.append((val, 0))
		elif type == PAM.PAM_PROMPT_ECHO_OFF:
			val = "s1e7r6d9a2" #getpass(query)
			resp.append((val, 0))
		elif type == PAM.PAM_PROMPT_ERROR_MSG or type == PAM.PAM_PROMPT_TEXT_INFO:
			print query
			resp.append(('', 0));
		else:
			return None

	return resp

service = 'login'

if len(sys.argv) == 2:
	user = sys.argv[1]
else:
	user = None

auth = PAM.pam()
auth.start(service)
if user != None:
	auth.set_item(PAM.PAM_USER, user)
auth.set_item(PAM.PAM_CONV, pam_conv)
try:
	auth.authenticate()
	auth.acct_mgmt()
except PAM.error, (resp, code):
	print 'Go away! (%s)' % resp
except:
	print 'Internal error'
else:
	print 'Good to go!'
