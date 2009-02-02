# -*- coding: utf-8 -*-

import os
import dbus
import struct

from zorg.consts import *
from zorg.parser import *
from zorg.utils import *
from zorg import modeline

# from pci/header.h
PCI_COMMAND             = 0x04
PCI_COMMAND_IO          = 0x1
PCI_COMMAND_MEMORY      = 0x2

PCI_BRIDGE_CONTROL      = 0x3e
PCI_BRIDGE_CTL_VGA      = 0x08

PCI_BASE_CLASS_DISPLAY  = 0x03

#PCI_BASE_CLASS_BRIDGE   = 0x06
PCI_CLASS_BRIDGE_PCI    = 0x0604

class PCIDevice:
    def __init__(self, name):
        self.name = name
        self.class_ = None
        self.bridge = None
        self.config = None

    def _readConfig(self, offset, size=1):
        if self.config is None:
            self.config = open(os.path.join(sysdir, self.name, "config")).read()

        return self.config[offset:offset+size]

    def readConfigWord(self, offset):
        data = self._readConfig(offset, 2)

        return struct.unpack("h", data)[0]

class VideoDevice:
    def __init__(self, deviceDir=None, busId=None):
        if deviceDir:
            self.bus = tuple(int(x, 16) for x in deviceDir.replace(".",":").split(":"))[1:4]
        else:
            self.bus = tuple(int(x) for x in busId.split(":")[1:4])
            deviceDir = "0000:%02x:%02x.%x" % self.bus

        self.vendor_id  = lremove(pciInfo(deviceDir, "vendor"), "0x").lower()
        self.product_id = lremove(pciInfo(deviceDir, "device"), "0x").lower()
        self.saved_vendor_id  = None
        self.saved_product_id = None

        self.driver = "vesa"
        self.package = "xorg-video"

        self.probe_result = {"flags" : "", "depths" : "16,24"}

        self.active_outputs = ["default"]
        self.modes = {"default" : "800x600"}
        self.depth = "16"
        self.desktop_setup = "single"

        self.driver_options = {}
        self.monitors = {}

        self._driver_packages = None

    def _driverPackages(self):
        if self._driver_packages is None:
            self._driver_packages = listDriverPackages()
        return self._driver_packages

    def getDict(self):
        info = {
            "bus-id" : "PCI:%d:%d:%d" % self.bus,
            "driver" : self.driver,
            "depth" : self.depth,
            "desktop-setup" : self.desktop_setup,
            "active-outputs" : ",".join(self.active_outputs),
        }

        for output, mode in self.modes.items():
            info["%s-mode" % output] = mode
            if self.monitors.has_key(output):
                info["%s-hsync" % output] = self.monitors[output].hsync
                info["%s-vref"  % output] = self.monitors[output].vref

        return info

    def chooseDriver(self):
        if isVirtual():
            print "We are in domU. Using fbdev driver."
            if os.path.exists("/dev/fb0"):
                self.driver = "fbdev"
            return

        for line in loadFile(DriversDB):
            if line.startswith(self.vendor_id + self.product_id):
                print "Device ID found in driver database."

                driverlist = line.rstrip("\n").split(" ")[1:]

                for drv in driverlist:
                    if package_sep in drv:
                        drvname, drvpackage = drv.split(package_sep, 1)
                        if drvpackage.replace("-", "_") in self._driverPackages():
                            self.driver = drvname
                            self.package = drvpackage
                            break

                    elif driverExists(drv):
                        self.driver = drv
                        break
                else:
                    self.driver = "vesa"

                print "Driver '%s' selected from '%s' package." % (self.driver, self.package)
                break
        else:
            # if could not find driver from driverlist try X -configure
            print "Running X server to query driver..."
            ret = run("/usr/bin/X", ":99", "-configure", "-logfile", "/var/log/xlog")
            if ret == 0:
                home = os.getenv("HOME", "")
                p = XorgParser()
                p.parseFile(home + "/xorg.conf.new")
                unlink(home + "/xorg.conf.new")
                sec = p.getSections("Device")
                if sec:
                    self.driver = sec[0].get("Driver")

                    print "Driver reported by X server is %s." % self.driver

    def query(self, withDriver=None):
        self.package = "xorg-video"

        if withDriver:
            if package_sep in withDriver:
                drvname, drvpackage = withDriver.split(package_sep, 1)
                if drvpackage.replace("-", "_") in self._driverPackages():
                    self.driver = drvname
                    self.package = drvpackage

            elif driverExists(withDriver):
                self.driver = withDriver

            else:
                self.chooseDriver()

        else:
            self.chooseDriver()

        self.enableDriver()

        self.probe_result = call(self.package, "Xorg.Driver", "probe", self.getDict())

        if self.probe_result is None:
            self.probe_result = {
                "flags":        "",
                "outputs":      "default",
                "tv-standards": ""
                }

            if self.driver in truecolor_cards:
                self.probe_result["depths"] = "24,16"
            else:
                self.probe_result["depths"] = "16,24"

            queryMonitor(self)

        depthlist = self.probe_result.get("depths", "16,24").split(",")
        self.depth = depthlist[0]

        #flags = self.probe_result["flags"].split(",")

    def enableDriver(self):
        oldpackage = enabledPackage()
        if self.package != oldpackage:
            if oldpackage.replace("-", "_") in self._driverPackages():
                call(oldpackage, "Xorg.Driver", "disable")

            call(self.package, "Xorg.Driver", "enable")

    def requestDriverOptions(self):
        self.driver_options = call(self.package, "Xorg.Driver", "getOptions", self.getDict())

    def isChanged(self):
        if self.saved_vendor_id and self.saved_product_id:
            return (self.vendor_id, self.product_id) != (self.saved_vendor_id, self.saved_product_id)
        return False

class Monitor:
    def __init__(self):
        self.vendor = ""
        self.model = "Default Monitor"
        self.hsync = "31.5-50"
        self.vref = "50-70"

def pciInfo(dev, attr):
    return sysValue(sysdir, dev, attr)

def call(package, model, method, *args):
    "Calls Comar methods"

    bus = dbus.SystemBus()
    app = package.replace("-", "_")

    try:
        object = bus.get_object("tr.org.pardus.comar", "/package/%s" % app, introspect=False)
        iface = dbus.Interface(object, "tr.org.pardus.comar.%s" % model)
    except dbus.exceptions.DBusException, e:
        print "Error:",
        print e
        return

    cmethod = getattr(iface, method)
    return cmethod(timeout=2**16-1, *args)

def getKeymapList():
    return os.listdir(xkb_path)

def driverExists(name):
    return os.path.exists(os.path.join(driver_path, "%s_drv.so" % name))

def listAvailableDrivers(d = driver_path):
    a = []
    if os.path.exists(d):
        for drv in os.listdir(d):
            if drv.endswith("_drv.so"):
                if drv[:-7] not in a:
                    a.append(drv[:-7])
    return a

def listDriverPackages():
    try:
        bus = dbus.SystemBus()
        object = bus.get_object("tr.org.pardus.comar", "/", introspect=False)
        iface = dbus.Interface(object, "tr.org.pardus.comar")

    except dbus.exceptions.DBusException, e:
        print "Error: %s" % e
        return []

    return iface.listModelApplications("Xorg.Driver")

def enabledPackage():
    try:
        return file("/var/lib/zorg/enabled_package").read()
    except IOError:
        return "xorg-video"

def queryPCI(vendor, device):
    f = file("/usr/share/misc/pci.ids")
    flag = 0
    company = ""
    for line in f.readlines():
        if flag == 0:
            if line.startswith(vendor):
                flag = 1
                company = line[5:].strip()
        else:
            if line.startswith("\t"):
                if line.startswith("\t" + device):
                    return company, line[6:].strip()
            elif not line.startswith("#"):
                flag = 0
    return None, None

def getPrimaryCard():
    devices = []
    bridges = []

    for dev in os.listdir(sysdir):
        device = PCIDevice(dev)
        device.class_ = int(pciInfo(dev, "class")[:6], 16)
        devices.append(device)

        if device.class_ == PCI_CLASS_BRIDGE_PCI:
            bridges.append(device)

    for dev in devices:
        for bridge in bridges:
            dev_path = os.path.join(sysdir, bridge.name, dev.name)
            if os.path.exists(dev_path):
                dev.bridge = bridge

    primaryBus = None
    for dev in devices:
        if (dev.class_ >> 8) != PCI_BASE_CLASS_DISPLAY:
            continue

        vga_routed = True
        bridge = dev.bridge
        while bridge:
            bridge_ctl = bridge.readConfigWord(PCI_BRIDGE_CONTROL)

            if not (bridge_ctl & PCI_BRIDGE_CTL_VGA):
                vga_routed = False
                break

            bridge = bridge.bridge

        if vga_routed:
            pci_cmd = dev.readConfigWord(PCI_COMMAND)

            if pci_cmd & (PCI_COMMAND_IO | PCI_COMMAND_MEMORY):
                primaryBus = dev.name
                break

    # Just to ensure that we have picked a device. Normally,
    # primaryBus might not be None here.
    if primaryBus is None:
        for dev in devices:
            if (dev.class_ >> 8) == PCI_BASE_CLASS_DISPLAY:
                primaryBus = dev.name
                break

    return primaryBus

def XProbe(dev):
    p = XorgParser()
    sec = XorgSection("Device")
    sec.set("Identifier", "Card0")
    sec.set("Driver", dev["driver"])
    sec.set("BusId", dev["bus-id"])

    if dev.has_key("driver-options"):
        sec.options.update(dev["driver-options"])

    p.sections.append(sec)

    sec = XorgSection("Screen")
    sec.set("Identifier", "Screen0")
    sec.set("Device", "Card0")

    if dev.has_key("depth"):
        sec.set("DefaultDepth", unquoted(dev["depth"]))

    p.sections.append(sec)

    open("/tmp/xorg.conf", "w").write(p.toString())

    ret = run("/usr/bin/X", ":99", "-probeonly", "-allowMouseOpenFail", \
            "-config", "/tmp/xorg.conf", \
            "-logfile", "/var/log/xlog", \
            "-logverbose", "6")
    unlink("/tmp/xorg.conf")
    if ret != 0:
        return

    return file("/var/log/xlog").readlines()

def queryDDC(adapter=0):
    from zorg import ddc
    edid = ddc.query(adapter)

    if not edid or not edid["eisa_id"]:
        return

    if edid["version"] != 1 and edid["revision"] != 3:
        return

    detailed = edid["detailed_timing"]

    hsync_min, hsync_max = detailed["hsync_range"]
    vref_min, vref_max = detailed["vref_range"]

    # FIXME: When subsystem is ready, review these.

    #modes = edid["standard_timings"] + edid["established_timings"]
    modes = list(edid["standard_timings"])

    m = modeline.calcFromEdid(edid)
    if m:
        dtmode = m["mode"] + (m["vfreq"],)
        modes.append(dtmode)

    res = set((x, y) for x, y, z in modes if x > 800 and y > 600)
    res = list(res)

    res.sort(reverse=True)

    res = ["%dx%d" % (x, y) for x, y in res]

    if hsync_max == 0 or vref_max == 0:
        hfreqs = vfreqs = []
        for w, h, vfreq in modes:
            vals = {
                "hPix" : w,
                "vPix" : h,
                "vFreq" : vfreq
            }
            m = modeline.ModeLine(vals)
            hfreqs.append(m["hFreq"] / 1000.0) # in kHz
            vfreqs.append(m["vFreq"])

        if len(hfreqs) > 2 and len(vfreqs) > 2:
            hfreqs.sort()
            vfreqs.sort()
            hsync_min, hsync_max = hfreqs[0], hfreqs[-1]
            vref_min, vref_max = vfreqs[0], vfreqs[-1]

    if hsync_max == 0 or vref_max == 0:
        hsync_min, hsync_max = 31.5, 50
        vref_min, vref_max = 50, 70

    mon = Monitor()
    mon.model = detailed.get("name", "Auto-detected Monitor")
    mon.hsync = "%s-%s" % (hsync_min, hsync_max)
    mon.vref  = "%s-%s" % (vref_min,  vref_max )

    if edid["eisa_id"]:
        for line in loadFile(MonitorsDB):
            l = line.split(";")
            if edid["eisa_id"].upper() == l[2].strip().upper():
                mon.hsync = l[3].strip()
                mon.vref  = l[4].strip()
                break

    return mon, res

def queryPanel(card):
    panel_w = 0
    panel_h = 0

    p = XorgParser()
    sec = XorgSection("Device")
    sec.set("Identifier", "Card0")
    sec.set("Driver", card.driver)
    p.sections.append(sec)

    sec = XorgSection("Monitor")
    sec.set("Identifier", "Monitor0")
    p.sections.append(sec)

    sec = XorgSection("Screen")
    sec.set("Identifier", "Screen0")
    sec.set("Device", "Card0")
    p.sections.append(sec)

    open("/tmp/xorg.conf", "w").write(p.toString())

    patterns = [
        "Panel size is",
        "Panel Size is",
        "Panel Size from BIOS:",
        "Panel size: ",
        "Panel Native Resolution is ",
        "Panel is a ",
        "Detected panel size via",
        "Detected panel size via BIOS: ",
        "Size of device LFP (local flat panel) is",
        "Size of device LFP",
        "Size of device DFP",
        "Virtual screen size determined to be ",
        "Detected LCD/plasma panel ("
    ]

    print "Running X server to query panel..."
    a = run("/usr/bin/X", ":99", "-probeonly", "-allowMouseOpenFail", \
            "-config", "/tmp/xorg.conf", \
            "-logfile", "/var/log/xlog")
    if a != 0:
        return

    f = file("/var/log/xlog")
    for line in f.readlines():
        for p in patterns:
            if p in line:
                b = line[line.find(p)+len(p):]
                panel_w = atoi(b)
                b = b[b.find("x")+1:]
                panel_h = atoi(b)
                break
    f.close()

    if panel_w or panel_h:
        print "Panel size reported by X server is %dx%d." % (panel_w, panel_h)

    if panel_w > 800 and panel_h > 600:
        return "%dx%d" % (panel_w, panel_h)
    else:
        return

def queryMonitor(device):
    result = queryDDC()
    if not result:
        result = queryDDC(1)

    modes = []
    if result:
        monitor, modes = result
    else:
        monitor = Monitor()

    if not modes:
        modes = ["800x600", "640x480"]

    # check lcd panel
    if device.driver in lcd_drivers:
        panel_mode = queryPanel(device)
        if panel_mode:
            modes[:0] = [panel_mode]

    device.monitors["default"] = monitor
    device.probe_result["default-modes"] = ",".join(modes)
    device.modes["default"] = modes[0]
