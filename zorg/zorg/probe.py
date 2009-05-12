# -*- coding: utf-8 -*-

import os
import dbus
import glob

from zorg import consts
from zorg.parser import *
from zorg.utils import *

sysdir = "/sys/bus/pci/devices/"

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

        self.driver = None
        self.package = None

        self.initial = False
        self.probe_result = {"flags" : "", "depths" : "16,24"}

        self.active_outputs = []
        self.modes = {}
        self.depth = None
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
            "driver" : self.driver or "",
            "depth" : self.depth or "",
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

        for line in loadFile(consts.drivers_file):
            if line.startswith(self.vendor_id + self.product_id):
                print "Device ID found in driver database."

                driverlist = line.rstrip("\n").split(" ")[1:]

                for drv in driverlist:
                    if consts.package_sep in drv:
                        drvname, drvpackage = drv.split(consts.package_sep, 1)
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
        self.package = None

        if withDriver:
            if consts.package_sep in withDriver:
                drvname, drvpackage = withDriver.split(consts.package_sep, 1)
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

        if self.package:
            self.probe_result = call(self.package, "Xorg.Driver", "probe", self.getDict())

            if self.probe_result is None:
                self.probe_result = {
                    "flags":        "",
                    "outputs":      "default",
                    "tv-standards": ""
                    }

                self.probe_result["depths"] = "16,24"

        depthlist = self.probe_result.get("depths", "16,24").split(",")
        # self.depth = depthlist[0]

    def enableDriver(self):
        oldpackage = enabledPackage()
        if self.package != oldpackage:
            if oldpackage and oldpackage.replace("-", "_") in self._driverPackages():
                call(oldpackage, "Xorg.Driver", "disable")

            call(self.package, "Xorg.Driver", "enable")

    def requestDriverOptions(self):
        if not self.package or self.package == "xorg-video":
            return
        self.driver_options = call(self.package, "Xorg.Driver", "getOptions", self.getDict())

    def isChanged(self):
        if self.saved_vendor_id and self.saved_product_id:
            return (self.vendor_id, self.product_id) != (self.saved_vendor_id, self.saved_product_id)
        return False

    def flags(self):
        return self.probe_result.get("flags", "").split(",")

    def needsScreenSection(self):
        flags = self.flags()

        return "norandr" in flags or self.depth is not None

    def needsModesLine(self):
        flags = self.flags()

        return "norandr" in flags or "no-modes-line" in flags

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
    return os.listdir(consts.xkb_symbols_dir)

def driverExists(name):
    return os.path.exists(os.path.join(consts.drivers_dir, "%s_drv.so" % name))

def listAvailableDrivers(d = consts.drivers_dir):
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
        return None

def getPrimaryCard():
    for boot_vga in glob.glob("%s/*/boot_vga" % sysdir):
        if open(boot_vga).read().startswith("1"):
            dev_path = os.path.dirname(boot_vga)
            return os.path.basename(dev_path)

    return None

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
