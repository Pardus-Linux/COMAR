# -*- coding: utf-8 -*-

import os

import piksemel

from zorg.parser import *
from zorg.probe import VideoDevice, Monitor
from zorg.utils import atoi

xorgConf = "/etc/X11/xorg.conf"
zorgConfigDir = "/var/lib/zorg"
zorgConfig = "config.xml"

def saveXorgConfig(card):
    parser = XorgParser()

    secModule = XorgSection("Module")
    secdri = XorgSection("dri")
    secFiles = XorgSection("Files")
    secFlags = XorgSection("ServerFlags")
    secDevice = XorgSection("Device")
    secScr = XorgSection("Screen")
    secLay = XorgSection("ServerLayout")

    parser.sections = [
        secModule,
        secdri,
        secFiles,
        secFlags,
        secLay,
        secScr,
        secDevice
    ]

    extmod = XorgSection("extmod")
    extmod.options = {"omit xfree86-dga" : unquoted()}
    secModule.sections = [extmod]

    secdri.set("Mode", unquoted("0666"))

    secFiles.set("RgbPath", "/usr/lib/X11/rgb")
    fontPaths = (
        "/usr/share/fonts/misc/",
        "/usr/share/fonts/dejavu/",
        "/usr/share/fonts/TTF/",
        "/usr/share/fonts/freefont/",
        "/usr/share/fonts/TrueType/",
        "/usr/share/fonts/corefonts",
        "/usr/share/fonts/Speedo/",
        "/usr/share/fonts/Type1/",
        "/usr/share/fonts/100dpi/",
        "/usr/share/fonts/75dpi/",
        "/usr/share/fonts/encodings/",
    )
    for fontPath in fontPaths:
        secFiles.add("FontPath", fontPath)

    secFlags.options = {
        "AllowEmptyInput" : "true",
        "AllowMouseOpenFail" : "true",
        "BlankTime" : "0",
        "StandbyTime" : "0",
        "SuspendTime" : "0",
        "OffTime" : "0"
    }

    info = card.getDict()

    #secDevice.set("Screen", screenNumber)
    secDevice.set("Identifier", "VideoCard")
    secDevice.set("Driver", card.driver)
    #secDevice.set("VendorName", dev.vendorName)
    #secDevice.set("BoardName", dev.boardName)
    secDevice.set("BusId", info["bus-id"])
    secDevice.options.update(card.driver_options)

    flags = card.probe_result["flags"].split(",")

    for output in card.active_outputs:
        identifier = "Monitor[%s]" % output

        monSec = XorgSection("Monitor")
        parser.sections.append(monSec)
        monSec.set("Identifier", identifier)

        if card.monitors.has_key(output):
            monSec.set("HorizSync", unquoted("%s - %s" % card.monitors[output].hsync))
            monSec.set("VertRefresh", unquoted("%s - %s" % card.monitors[output].vref))

        if "randr12" in flags:
            secDevice.options["Monitor-%s" % output] = identifier
            if card.modes.has_key(output):
                monSec.options["PreferredMode"] = card.modes[output]
            monSec.options["Enabled"] = "true"

    secScr.set("Identifier", "Screen")
    secScr.set("Device", "VideoCard")
    secScr.set("Monitor", "Monitor[%s]" % card.active_outputs[0])
    secScr.set("DefaultDepth", atoi(card.depth))

    subsec = XorgSection("Display")
    subsec.set("Depth", atoi(card.depth))

    if "no-modes-line" not in flags:
        output = card.active_outputs[0]
        if card.modes.has_key(output):
            subsec.set("Modes", card.modes[output], "800x600", "640x480")

    secScr.sections = [subsec]

    secLay.set("Identifier", "Layout")
    secLay.set("Screen", "Screen")

    f = open(xorgConf, "w")
    f.write(parser.toString())
    f.close()

def addTag(p, name, data):
    t = p.insertTag(name)
    t.insertData(data)

def getDeviceInfo(busId):
    configFile = os.path.join(zorgConfigDir, zorgConfig)
    if not os.path.exists(configFile):
        return

    doc = piksemel.parse(configFile)

    cardTag = None
    for tag in doc.tags("Card"):
        if tag.getAttribute("busId") == busId:
            cardTag = tag
            break

    if not cardTag:
        return

    device = VideoDevice(busId=busId)

    driversTag = cardTag.getTag("Drivers")
    drivers = []
    for tag in driversTag.tags("Driver"):
        drvname = tag.firstChild().data()
        drvpackage = tag.getAttribute("package")
        if drvpackage != "xorg-video":
            drvname += ":%s" % drvpackage

        drivers.append(drvname)

    probeResultTag = cardTag.getTag("ProbeResult")
    probeResult = {}
    for tag in probeResultTag.tags("Value"):
        key = tag.getAttribute("key")
        child = tag.firstChild()
        if child:
            value = child.data()
        else:
            value = ""
        probeResult[key] = value

    monitorsTag = cardTag.getTag("Monitors")
    for tag in monitorsTag.tags("Monitor"):
        mon = Monitor()
        mon.eisaid = tag.getAttribute("id")
        output = tag.getAttribute("output")
        device.monitors[output] = mon

        hsync = tag.getTag("HorizSync")
        min = hsync.getAttribute("min")
        max = hsync.getAttribute("max")
        mon.hsync = (min, max)

        vref = tag.getTag("VertRefresh")
        min = vref.getAttribute("min")
        max = vref.getAttribute("max")
        mon.vref = (min, max)

    activeConfigTag = cardTag.getTag("ActiveConfig")

    driverTag = activeConfigTag.getTag("Driver")
    device.driver = driverTag.firstChild().data()
    device.package = driverTag.getAttribute("package")

    device.depth = activeConfigTag.getTagData("Depth")

    activeOutputs = []
    modes = {}
    for tag in activeConfigTag.tags("Output"):
        name = tag.firstChild().data()
        mode = tag.getAttribute("mode")
        activeOutputs.append(name)
        if mode:
            modes[name] = mode

    device.desktop_setup = activeConfigTag.getTagData("DesktopSetup")

    device.driverlist = drivers
    device.probe_result = probeResult
    device.active_outputs = activeOutputs
    device.modes = modes

    return device

def saveDeviceInfo(card):
    if not os.path.exists(zorgConfigDir):
        os.mkdir(zorgConfigDir, 0755)

    configFile = os.path.join(zorgConfigDir, zorgConfig)

    try:
        doc = piksemel.parse(configFile)
    except OSError:
        doc = piksemel.newDocument("ZORG")

    info = card.getDict()

    for tag in doc.tags("Card"):
        if tag.getAttribute("busId") == info["bus-id"]:
            tag.hide()
            break

    cardTag = doc.insertTag("Card")
    cardTag.setAttribute("busId", info["bus-id"])

    #addTag(cardTag, "VendorId", card.vendor_id)
    #addTag(cardTag, "ProductId", card.product_id)

    drivers = cardTag.insertTag("Drivers")
    for driver in card.driverlist:
        if ":" in driver:
            drv, pkg = driver.split(":", 1)
        else:
            drv = driver
            pkg = "xorg-video"

        d = drivers.insertTag("Driver")
        d.setAttribute("package", pkg)
        d.insertData(drv)

    probeResult = cardTag.insertTag("ProbeResult")
    for key, value in card.probe_result.items():
        t = probeResult.insertTag("Value")
        t.setAttribute("key", key)
        if value:
            t.insertData(value)

    monitors = cardTag.insertTag("Monitors")
    for output, monitor in card.monitors.items():
        monitorTag = monitors.insertTag("Monitor")
        monitorTag.setAttribute("id", monitor.eisaid)
        monitorTag.setAttribute("output", output)

        min, max = monitor.hsync
        hor = monitorTag.insertTag("HorizSync")
        hor.setAttribute("min", min)
        hor.setAttribute("max", max)

        min, max = monitor.vref
        ver = monitorTag.insertTag("VertRefresh")
        ver.setAttribute("min", min)
        ver.setAttribute("max", max)

    config = cardTag.insertTag("ActiveConfig")

    driver = config.insertTag("Driver")
    driver.setAttribute("package", card.package)
    driver.insertData(card.driver)

    addTag(config, "Depth", card.depth)

    outName = card.active_outputs[0]
    outMode = card.modes.get(outName)
    output = config.insertTag("Output")
    if outMode:
        output.setAttribute("mode", outMode)
    output.insertData(outName)

    addTag(config, "DesktopSetup", card.desktop_setup)

    if card.desktop_setup != "single":
        outName = card.active_outputs[1]
        outMode = card.modes.get(outName)
        output = config.insertTag("SecondOutput")
        if outMode:
            output.setAttribute("mode", outMode)
        output.insertData(outName)

    f = file(configFile, "w")
    f.write(doc.toPrettyString())
    f.close()
