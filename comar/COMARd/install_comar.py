#!/usr/bin/python
# -*- coding: utf-8 -*-

# standart python modules
import os, sys
import shutil
import os.path
import dircache

# COMAR modules
import comar_global

PATH_MODLANG = { "class":"ObjHook", "path":comar_global.comar_modpath + "/langdrv", "signature":"_HOOK", "files":[] }
PATH_MODCONN = { "class":"ExtConnector", "path":comar_global.comar_modpath + "/connector", "signature":"PROTOCOL", "files":[] }
PATH_MODTAD	 = { "class":"DefaultTTSHandler", "path":comar_global.comar_modpath + "/ttshandlers", "signature":"HANDLERS", "files":[] }
PATH_MODAPI  = { "class":"CSL Library", "path":comar_global.comar_modpath + "/capi", "signature":"_APICLASS", "files":[] }
PATH_MODOM  = { "class":"OM Driver", "path":comar_global.comar_modpath + "/om_drivers", "signature":"OM_BINDINGS", "files":[] }
PATH_AUTH  = { "class":"Auth/Crypto/Digest/Sign Modules", "path":comar_global.comar_modpath + "/auth", "signature":"DIGEST_CLASSES", "files":[] }

MODS = [PATH_MODLANG, PATH_MODCONN, PATH_MODTAD, PATH_MODAPI, PATH_MODOM, PATH_AUTH]

COMARD	= "/COMARd.py"
COMAR_PATH = os.getcwd()
COMAR_LIBS = comar_global.comar_libpath
COMAR_COMP = []

opt_dry_run = 0
opt_symlink = 1

def install(src,dest):
	global opt_dry_run, opt_symlink
	if opt_dry_run:
		print "Copy '%s' to '%s'." % (src,dest)
		return
		
	if os.path.isfile(dest) or os.path.islink(dest):
		os.unlink(dest)

	if opt_symlink:
		os.symlink(src, dest)
	else:
		shutil.copyfile(src,dest)

def makepath(p):
	global opt_dry_run
	ppart = ""
	for subdir in p.split("/"):
		if subdir != "":
			ppart += "/" + subdir
			if not os.path.isdir(ppart):
				if opt_dry_run:
					print "mkdir '%s'" % (ppart)
				else:
					os.makedirs(ppart, mode=0700)
			else:
				pass
	#print "Set directory %s permissions to 0700" % (ppart)
	if not opt_dry_run:
		os.chmod(ppart, 0700)
		os.chown(ppart, 0, 0)

def collectPyFiles(root = ""):
	dirlist = []
	dl = dircache.listdir(root)
	for i in dl:
		ai = root + "/" + i
		if os.path.isfile(ai):
			if ai[-3:] == ".py":
				dirlist.append(ai)
		elif os.path.isdir(ai):
			if i[0] != ".":
				ret = collectPyFiles(ai)
				dirlist.extend(ret)

	return dirlist[:]

def collectDepends(fn, file, pdir, cp = None):
	global COMARD, COMAR_PATH
	deps = []
	if cp == None:
		cp = COMAR_PATH
	for line in file:
		line = line.strip()
		if line.find('#') > -1:
			line = line[:line.find('#')].strip()
		if line[:6] == "import":
				#print "newline:", line

			imps = line[7:].split(",")
			for dep in imps:
				#print "Checking Dependency %s for file: %s over %s" % (dep, fn, pdir)
				if os.path.isfile(pdir + "/" + dep + ".py"):
					if pdir != cp:
						#print "\tFound Dependency: ", pdir + "/" + dep + ".py"
						fd = open(pdir + "/" + dep + ".py")
						lines = fd.readlines()
						dp = collectDepends(pdir + "/" + dep + ".py", lines, pdir)
						del lines
						fd.close()
						deps.extend(dp)
						deps.append(pdir + "/" + dep + ".py")
		elif line.find("__import__") > -1:
			lin = line.strip()
			imp = lin[lin.find("__import__") + 10:].strip()
			x = 0
			dep = None
			for i in imp:
				if i in "'\"":
					dep = imp[x + 2: imp.find(i, x + 2)]
					break
				x += 0
			if dep:
				#print "Imp module:", imp, dep
				if os.path.isfile(pdir + "/" + dep + ".py"):
					if pdir != cp:
						#print "\tFound Dependency: ", pdir + "/" + dep + ".py"
						fd = open(pdir + "/" + dep + ".py")
						lines = fd.readlines()
						dp = collectDepends(pdir + "/" + dep + ".py", lines, pdir)
						del lines
						fd.close()
						deps.extend(dp)
						deps.append(pdir + "/" + dep + ".py")
	return deps

def main():
	global MODS, COMARD, COMAR_PATH, COMAR_LIBS, STATIC_DATA
	if not os.path.isfile(COMAR_PATH + COMARD):
		print "You must run this to COMARd.py root path"
		sys._exit(1)
	makepath(comar_global.comar_data)
	makepath(comar_global.comar_libpath)
	dl = collectPyFiles(COMAR_PATH)
	crossList = {}
	deps = []
	for file in dl:
		if file[-len(COMARD):] != COMARD:
			fd = open(file, "r")
			lines = fd.readlines()
			bit = 0
			for l in lines:
				for mod in MODS:
					see = mod["signature"]
					if l[:len(see)] == see:
						depends = collectDepends(os.path.basename(file), lines, os.path.dirname(file))
						mod["files"].append(file[:])
						mod["files"].extend(depends)
						bit = 1
						break
				if bit == 1:
					break
	fd = open(COMAR_PATH + COMARD, "r")
	lines = fd.readlines()

	dp = collectDepends(COMAR_PATH + COMARD, lines, COMAR_PATH, "")
	rv = { "class":"COMAR Main Components", "path":COMAR_LIBS, "signature":"", "files":dp }
	MODS.append(rv)

	for mod in MODS:
		print mod["class"],"MODULES: "
		p = mod["path"]
		print "\tDestination Dir:", p
		makepath(p)
		for f in mod["files"]:
			fpart = os.path.basename(f)
			print "\t\t", f
			install(f, p + "/" + fpart)
		print ""

	print "Creating Data Directories:"
	for var in dir(comar_global):
		#print var
		if var[0:2] != '__':
			attr = getattr(comar_global, var)
			p = attr
			try:
				if p[0] == "/":
					print "\tData directory:", p
					makepath(p)
			except:
				pass
	    
	# COMARd.py'yi de kopyalayalım
	install(COMAR_PATH+COMARD,
		COMAR_LIBS+COMARD)
	# om dtd kopyalayalim
	install(COMAR_PATH+"/om_dtd/comar.xml", comar_global.comar_om_dtd + "/comar.xml")
	print "Installation successfull.."

#
if __name__ == "__main__":
	if "--test" in sys.argv[1:]:
		opt_dry_run = 1
	if "--copy" in sys.argv[1:]:
		opt_symlink = 0
	main()
