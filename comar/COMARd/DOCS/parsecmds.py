#!/bin/python
import sys
fd = open("OPLIST.txt")
ops = fd.readlines()
src_sess = {}
dst_sess = {}

mode = 1
try:
	if sys.argv[1] == "--ifcmds":
		mode = 0
except:
	pass

for l in ops:
	op = l[:l.find(":")].strip()
	cmd = l[l.find(":")+1:l.find(".")].strip()
	Dir = l[l.find(".")+1:l.find(":", l.find("."))].strip()
	ack = l[l.find(":",l.find("."))+1:].strip()
	#print "%s/%s/%s/%s" % (op, cmd, Dir, ack)
	dira = Dir.split(",")
	for i in dira:
		lv = i.split("->")[0]
		rv = i.split("->")[1]
		#print Dir, "=", lv,rv
		if not src_sess.has_key(lv):
			src_sess[lv] = []
		src_sess[lv].append([rv, op, cmd, ack])
		if not dst_sess.has_key(rv):
			dst_sess[rv] = []
		dst_sess[rv].append([lv, op, cmd, ack])

for i in src_sess.keys():
	print i, "->"
	fa = open("CMDS_%s.txt" % (i), "w")
	for j in src_sess[i]:
		if mode:
			print "['%s'], # %s->%s %s" % (j[1], i, j[0], j[2])
		else:
			print "if cmd == '%s': # %s->%s %s" % (j[1], i, j[0], j[2])
		fa.write("to   %8s, %-10s %-18s: %s\n" % (j[0], j[1], j[2], j[3]))
	fa.close()

for i in dst_sess.keys():
	print "->", i
	fa = open("CMDS_%s.txt" % (i), "a")
	for j in dst_sess[i]:
		fa.write("from %8s, %-10s %-18s: %s\n" % (j[0], j[1], j[2], j[3]))
		if mode:
			print "['%s'], # %s->%s %s" % (j[1], j[0],i, j[2])
		else:
			print "if cmd == '%s': # %s->%s %s" % (j[1], j[0],i, j[2])
	fa.close()
