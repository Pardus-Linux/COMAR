#!/usr/bin/python

import sys, CSLParser

debuglevel = 0
mode = ""
opts = sys.argv
max_opt = len(opts)
curr = 0
prms = {}

while curr < max_opt:
	opt = opts[curr]
	if opt == "-r":
		mode = "run"
		method = opts[curr+1]
		curr += 1
	elif opt == "-t":
		mode = "parse"
	elif opt == "-d":
		debuglevel += opts[curr+1]
		curr += 1
	elif opt == "-p":
		prm = opts[curr+1]
		prm = prm.split("=")
		prms[prm[0]] = prm[1]
	curr += 1
if len(sys.argv) < 3 or mode == "":
	print """Usage: csl <-r <method>| -p> [options] <filename>\nOptions:\n
	-p parameter=value		Set runtime parameter to value, can be repeat..
	-w variable				Watch variable..
	"""

if mode == "run":
	print "run:", method, prms

if mode == "parse":
	x = CSLParser.CSLParse(file = sys.argv[-1])
	Tbl = { "A":x.ATbl, "F":x.FTbl, "I": x.ITbl, "N":x.NTbl, "O":x.OTbl, "Q":x.QTbl }

	for i in Tbl.keys():
		print "TBL:", i
		ik = Tbl[i].keys()
		ik.sort()
		for j in ik:
			if i in "INQ":
				print "%s->%s " % (j, Tbl[i][j]),
			elif i == "O":
				src = Tbl[i][j]["src"]
				dst = Tbl[i][j]["dst"]
				op  = Tbl[i][j]["op"]
				if src[0:2] == "$I":
					src = Tbl["I"][src]
				if dst[0:2] == "$I":
					dst = Tbl["I"][dst]
				if src[0:2] == "$Q":
					src = "'%s'" % Tbl["Q"][src]
				if dst[0:2] == "$Q":
					dst = "'%s'" % Tbl["Q"][dst]
				if src[0:2] == "$N":
					src = Tbl["N"][src]
				if dst[0:2] == "$N":
					dst = Tbl["N"][dst]
				print "%s = %s %s %s (%s)" % (j, src, op, dst, Tbl[i][j])
			else:
				print "%s->%s " % (j, Tbl[i][j])
