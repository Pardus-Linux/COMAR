#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import os
import popen2

# api
def unlink(path):
	try:
		os.unlink(path)
	except:
		pass

def capture(cmd):
	out = []
	a = popen2.Popen4(cmd)
	while 1:
		b = a.fromchild.readline()
		if b == None or b == "":
			break
		out.append(b)
	return (a.wait(), out)

def grepini(lines, sect, key):
	flag = 0
	for line in lines:
		if flag == 0:
			if line.find(sect) != -1:
				flag = 1
		else:
			if line.find(key) != -1:
				return line.split()[-1].strip('"')
	return None

def atoi(s):
	# python'da bunu yapacak fonksiyon bulamadım
	# int() sayı olmayan karaktere rastladığında pörtlüyor
	t = ""
	for c in s.lstrip():
		if c in "0123456789":
			t += c
		else:
			break
	try:
		ret = int(t)
	except:
		ret = 0
	return ret

def write_tmpl(tmpl, keys, fname):
	f = file(fname, "w")
	f.write(tmpl % keys)
	f.close()

### modeline calc ###

def GetInt(name, dict, default=0):
    str = dict.get(name , default)
    try:
        return int(str)
    except:
        return default

# _ GetFloat ___________________________________________________________
def GetFloat(name, dict, default=0.0):
    str = dict.get(name , default)
    try:
        return float(str)
    except:
        return default


# _ ModeLine ___________________________________________________________
def ModeLine(dict={}):
    '''
    This routine will calculate XF86Config Modeline entries.
    The Parameters are supplies as a dictionary due to the large number.
    The Calculated values are also returned in dictionary form.

    The parameter dictionary entries are:
    hPix       Horizontal displayed pixels    Default: 1280)
    hSync      Horizontal sync in uSec        Default: 1)
    hBlank     Horizontal blanking in uSec    Default: 3)
    vPix       Vertical displayed pixels      Default: 960)
    vFreq      Vertical scan frequency in Hz  Default: 75)
    vSync      Vertical sync in uSec          Default: 0)
    vBlank     Vertical blanking in uSec      Default: 500)
    v4x3       Constrain h/v to 4/3           Default: 0 (not constrained)

    hRatio1    Horizontal front poarch ratio  Default: 1)
    hRatio2    Horizontal sync ratio          Default: 4)
    hRatio3    Horizontal back poarch ratio   Default: 7)
    vRatio1    Vertical front poarch ratio    Default: 1)
    vRatio2    Vertical sync ratio            Default: 1)
    vRatio3    Vertical back poarch ratio     Default: 10)

    If v4x3="1" vPix is ignored.

    If any of the following:hSync, hBlanking, vSync, vBlanking
    are not specified then they are set based on the ratios,
    at a minimum is is best to specify either sync or blanking.

    The return dictionary entries are:
    The "entry" value is really all that is needed
    entry     Modeline entry string

    These are the values that make up the modeline entry
    dotClock    Dot clock in MHz
    hPix        Horizontal displayed pixels
    hFreq       Horizontal scan frequency in Hz.
    hTim1       Horizontal front poarch pixels
    hTim2       Horizontal sync pixels
    hTim3       Horizontal back poarch pixels
    vPix        Vertical displayed pixels
    vFreq       Vertical scan frequency in Hz.
    vTim1       Vertical front poarch pixels
    vTim2       Vertical sync pixels
    vTim3       Vertical back poarch pixels
    '''
    results = {}
    hPix    = GetInt(  "hPix"    , dict, 1280)
    hSync   = GetFloat("hSync"   , dict, 1)
    hBlank  = GetFloat("hBlank"  , dict, 3)
    hRatio1 = GetFloat("hRatio1" , dict, 1)
    hRatio2 = GetFloat("hRatio2" , dict, 4)
    hRatio3 = GetFloat("hRatio3" , dict, 7)
    vPix    = GetInt(  "vPix"    , dict, 960)
    vFreq   = GetFloat("vFreq"   , dict, 75)
    vSync   = GetFloat("vSync"   , dict, 0)
    vBlank  = GetFloat("vBlank"  , dict, 500)
    vRatio1 = GetFloat("vRatio1" , dict, 1)
    vRatio2 = GetFloat("vRatio2" , dict, 1)
    vRatio3 = GetFloat("vRatio3" , dict, 10)
    if (dict.has_key("v4x3")    == 0):
        v4x3        = ""
    else:
        v4x3        = "checked"
        vPix        = int(hPix) / 4 * 3

    vSyncUs = vSync / 1000000.0
    vBlankUs = vBlank / 1000000.0

    vRatioT = vRatio1 + vRatio2 + vRatio3
    if   ((vSyncUs > 0.0) and (vBlankUs > 0.0)):
        vRatio2 = (vRatio1 + vRatio3) * (vSyncUs / (vBlankUs - vSyncUs))
        vRatioT = vRatio1 + vRatio2 + vRatio3
    elif ((vSyncUs > 0.0) and (vBlankUs <= 0.0)):
        vBlankUs = vSyncUs * (vRatioT / vRatio2)
    elif ((vSyncUs <= 0.0) and (vBlankUs > 0.0)):
        vSyncUs = vBlankUs * (vRatio2 / vRatioT)

    vBase = 1.0 / vFreq
    vBase = (vPix / (vBase - vBlankUs)) * vBase
    vBase = (vBase - vPix) / vRatioT

    vTim1 = vPix  + int((vBase * vRatio1) + 1.0)
    vTim2 = vTim1 + int((vBase * vRatio2) + 1.0)
    vTim3 = vTim2 + int((vBase * vRatio3) + 1.0)

    hFreq    = (vTim3 * vFreq)

    hSyncUs  = hSync / 1000000.0
    hBlankUs = hBlank / 1000000.0

    hPix    = ((hPix + 7) / 8) * 8

    hRatioT = hRatio1 + hRatio2 + hRatio3
    if   ((hSyncUs > 0.0) and (hBlankUs > 0.0)):
        hRatio2 = (hRatio1 + hRatio3) * (hSyncUs / (hBlankUs - hSyncUs))
        hRatioT = hRatio1 + hRatio2 + hRatio3
    elif ((hSyncUs > 0.0) and (hBlankUs <= 0.0)):
        hBlankUs = hSyncUs * (hRatioT / hRatio2)
    elif ((hSyncUs <= 0.0) and (hBlankUs > 0.0)):
        hSyncUshBlankUs = hBlankUs * (hRatio2 / hRatioT)

    hBase = 1.0 / hFreq
    hBase = (hPix / (hBase - hBlankUs)) * hBase
    hBase = (hBase - hPix) / hRatioT

    hTim1 = hPix  + ((int((hBase * hRatio1)+8.0) / 8) * 8)
    hTim2 = hTim1 + ((int((hBase * hRatio2)+8.0) / 8) * 8)
    hTim3 = hTim2 + ((int((hBase * hRatio3)+8.0) / 8) * 8)

    dotClock = (hTim3 * vTim3 * vFreq) / 1000000.0
    
    hFreqKHz = hFreq / 1000.0

    results = {}
    results["entry"]    = '''\
# %(hPix)dx%(vPix)d @ %(vFreq)dHz, %(hFreqKHz)6.2f kHz hsync
	Mode "%(hPix)dx%(vPix)d"
		DotClock  %(dotClock)8.2f
		HTimings  %(hPix)d %(hTim1)d %(hTim2)d %(hTim3)d
		VTimings  %(vPix)d %(vTim1)d %(vTim2)d %(vTim3)d
	EndMode\
    ''' % vars()
    results["hPix"]     = hPix
    results["vPix"]     = vPix
    results["vFreq"]    = vFreq
    results["hFreq"]    = hFreq
    results["dotClock"] = dotClock
    results["hTim1"]    = hTim1
    results["hTim2"]    = hTim2
    results["hTim3"]    = hTim3
    results["vTim1"]    = vTim1
    results["vTim2"]    = vTim2
    results["vTim3"]    = vTim3
    
    return results

def calcModeLine(w, h, vfreq):
	vals = {}
	vals["hPix"] = w
	vals["vPix"] = h
	vals["vFreq"] = vfreq
	m = ModeLine(vals)
	return m["entry"]

### Asıl betik aşağıda ###

template_display = """
Section "ServerLayout"
	Identifier "COMAR Configured Layout"
	Screen   0 "Screen0" 0 0
EndSection

Section "Monitor"
	Identifier "Monitor0"
EndSection

Section "Screen"
	Identifier "Screen0"
	Device     "Card0"
EndSection

Section "Device"
	Identifier "Card0"
	Driver     "%(DRIVER)s"
EndSection

"""

template_main = """
Section "Module"
	Load "dbe"  	# Double buffer extension
	SubSection "extmod"
		Option "omit xfree86-dga"   # don't initialise the DGA extension
	EndSubSection
	Load "type1"
	Load "freetype"
	Load "glx"
	Load "dri"
	Load "v4l"
	%(SYNAPTICS_MOD)s
EndSection

Section "dri"
	Mode 0666
EndSection

Section "Files"
	RgbPath  "/usr/lib/X11/rgb"
	FontPath "/usr/share/fonts/ttf-bitstream-vera/"
	FontPath "/usr/share/fonts/misc/"
	FontPath "/usr/share/fonts/75dpi/:unscaled"
	FontPath "/usr/share/fonts/100dpi/:unscaled"
	FontPath "/usr/share/fonts/Speedo/"
	FontPath "/usr/share/fonts/Type1/"
	FontPath "/usr/share/fonts/TrueType/"
	FontPath "/usr/share/fonts/TTF/"
	FontPath "/usr/share/fonts/freefont/"
	FontPath "/usr/share/fonts/75dpi/"
	FontPath "/usr/share/fonts/100dpi/"
	FontPath "/usr/share/fonts/corefonts"
	FontPath "/usr/share/fonts/encodings/"
EndSection

Section "ServerFlags"
	Option     "AllowMouseOpenFail" "True"
EndSection

Section "InputDevice"
	Identifier "Keyboard0"
	Driver     "kbd"
	Option     "AutoRepeat" "500 30"
	Option     "XkbModel" "pc105"
	Option     "XkbLayout" "tr"
EndSection

Section "InputDevice"
	Identifier "Mouse0"
	Driver     "mouse"
	Option     "Protocol" "ExplorerPS/2"
	Option     "Device" "/dev/input/mice"
	Option     "ZAxisMapping" "4 5"	
	Option     "Buttons" "5"
EndSection

%(SYNAPTICS_SEC)s

Section "Device"
	Identifier "DisplayController0"
	Driver     "%(DRIVER)s"
	Option     "RenderAccel" "true"
EndSection

Section "Screen"
	Identifier "Screen0"
	Device     "DisplayController0"
	Monitor    "Monitor0"
	DefaultDepth 16
	Subsection "Display"
		Depth    8
		Modes    %(MODES)s
	EndSubsection
	Subsection "Display"
		Depth    16
		Modes    %(MODES)s
	EndSubsection
	Subsection "Display"
		Depth    24
		Modes    %(MODES)s
	EndSubsection
EndSection

Section "ServerLayout"
	Identifier  "Simple Layout"
	Screen      "Screen0"
	InputDevice "Mouse0" "CorePointer"
	%(SYNAPTICS_LAY)s
	InputDevice "Keyboard0" "CoreKeyboard"
EndSection

Section "Monitor"
	Identifier  "Monitor0"
	VendorName  "Vendor"
	ModelName   "Model"
	HorizSync    %(HSYNC)s
	VertRefresh  %(VREF)s
	Option      "DPMS" "off"
	
%(MODELINES)s
	
EndSection
"""

template_synaptics = """
Section "InputDevice"
	Identifier "Mouse1"
	Driver     "synaptics"
	Option     "Protocol" "auto-dev"
	Option     "Device" "/dev/input/mouse0"
	Option     "ZAxisMapping" "4 5"
	Option     "Buttons" "5"
	# "Option    "AccelFactor" "0.04"
EndSection
"""

class Monitor:
	def __init__(self):
		self.wide = 0
		self.panel_w = 0
		self.panel_h = 0
		self.hsync_min = 0
		self.hsync_max = 0
		self.vert_min = 0
		self.vert_max = 0
		self.modes = []
		self.res = ""

def queryPanel(mon):
	patterns = [
	"Panel size is",
	"Panel Size is",
	"Panel Size from BIOS:",
	"Detected panel size via",
	"Size of device LFP (local flat panel) is",
	"Size of device LFP",
	"Size of device DFP",
	"Detected LCD/plasma panel ("
	]
	a = capture("/usr/bin/X -probeonly -allowMouseOpenFail -logfile /var/log/xlog")
	if a[0] != 0:
		print "X -probeonly failed!"
		return
	f = file("/var/log/xlog")
	for line in f.readlines():
		for p in patterns:
			if p in line:
				b = line[line.find(p)+len(p):]
				mon.panel_w = atoi(b)
				b = b[b.find("x")+1:]
				mon.panel_h = atoi(b)
				break
	f.close()
	return None

def queryDDC():
	mon = Monitor()
	ddc = capture("/usr/sbin/ddcxinfos")
	if ddc[0] != 0:
		print "ddcxinfos failed!"
		return mon
	
	for line in ddc[1]:
		t = line.find("truly")
		if t != -1:
			mon.wide = atoi(line[t+6:])
		t = line.find("kHz HorizSync")
		if t != -1:
			mon.hsync_min = atoi(line)
			mon.hsync_max = atoi(line[line.find("-") + 1:])
		t = line.find("Hz VertRefresh")
		if t != -1:
			mon.vert_min = atoi(line)
			mon.vert_max = atoi(line[line.find("-") + 1:])
		if line[:8] == "ModeLine":
			mon.modes.append("    " +line)
	
	for m in mon.modes:
		t = m[m.find("ModeLine"):].split()[1]
		if t not in mon.res:
			mon.res = t + " " + mon.res
	
	if mon.res == "":
		mon.res = '"800x600" "640x480"'
	
	return mon

def queryMouse(keys):
	keys["SYNAPTICS_MOD"] = ""
	keys["SYNAPTICS_SEC"] = ""
	keys["SYNAPTICS_LAY"] = ""
	try:
		a = file("/proc/bus/input/devices")
		for line in a.readlines():
			if "SynPS/2" in line or "AlpsPS/2" in line:
				keys["SYNAPTICS_MOD"] = 'Load "synaptics"'
				keys["SYNAPTICS_LAY"] = 'InputDevice "Mouse1" "SendCoreEvents"'
				keys["SYNAPTICS_SEC"] = template_synaptics
		a.close()
	except:
		pass

# om call

xorg_conf = "/etc/X11/xorg.conf"

def configureDisplay():
	#if os.path.exists(xorg_conf):
	#	return
	
	# probe monitor freqs
	mon = queryDDC()
	# defaults for the case where ddc fails
	if mon.hsync_min == 0 or mon.vert_min == 0:
		mon.hsync_min = 31.5
		mon.hsync_max = 50
		mon.vert_min = 50
		mon.vert_max = 70
	
	# detect graphic card
	# if discover db has no data, try X -configure
	a = capture("/usr/bin/discover --data-path=xfree86/server/device/driver --data-version=4.3.0 display")
	if a[1][0] == '\n' or a[0] > 0:
		a = capture("/usr/bin/X -configure -logfile /var/log/xlog")
		if a[0] != 0:
			print "X -configure failed!"
			return -1
		home = os.getenv("HOME", "")
		f = file(home + "/xorg.conf.new")
		conf = f.readlines()
		f.close()
		unlink(home + "/xorg.conf.new")
		drv = grepini(conf, 'Section "Device"', "\tDriver")
	else:
		drv = a[1][0].rstrip('\n')
	
	# check lcd panel
	drivers = [ "nv", "nvidia", "ati", "via", "i810", "sis" ]
	if drv in drivers:
		write_tmpl(template_display, { "DRIVER": drv }, xorg_conf)
		queryPanel(mon)
	
	keys = {}
	keys["DRIVER"] = drv
	keys["HSYNC"] = str(mon.hsync_min) + "-" + str(mon.hsync_max)
	keys["VREF"] = str(mon.vert_min) + "-" + str(mon.vert_max)
	if mon.panel_h and mon.panel_w:
		keys["MODELINES"] = calcModeLine(mon.panel_w, mon.panel_h, 60)
		keys["MODES"] = '"%dx%d" "800x600" "640x480" "1024x768"' % (mon.panel_w,mon.panel_h)
	else:
		keys["MODELINES"] = "".join(mon.modes)
		keys["MODES"] = mon.res
	
	queryMouse(keys)
	
	write_tmpl(template_main, keys, xorg_conf)

# test
configureDisplay()

