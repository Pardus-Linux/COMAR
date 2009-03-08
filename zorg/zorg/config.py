# -*- coding: utf-8 -*-

import os

import piksemel

from zorg.consts import *
from zorg.parser import *
from zorg.probe import VideoDevice, Monitor
from zorg.utils import *

def saveXorgConfig(card):
    parser = XorgParser()

    secModule = XorgSection("Module")
    secFlags = XorgSection("ServerFlags")
    secDevice = XorgSection("Device")
    secScr = XorgSection("Screen")
    secLay = XorgSection("ServerLayout")

    parser.sections = [
        secModule,
        secFlags,
        secDevice,
    ]

    if card.needsScreenSection():
        parser.sections.extend([secScr, secLay])

    extmod = XorgSection("extmod")
    extmod.options = {"omit xfree86-dga" : unquoted()}
    secModule.sections = [extmod]

    secFlags.options = {
        "AllowMouseOpenFail" : "true",
        "BlankTime" : "0",
        "StandbyTime" : "0",
        "SuspendTime" : "0",
        "OffTime" : "0"
    }

    if jailEnabled():
        jailOpts = {
                "DontVTSwitch" : "true",
                "DontZap" : "true"
                }
        secFlags.options.update(jailOpts)

    info = card.getDict()

    secDevice.set("Identifier", "VideoCard")
    if card.driver:
        secDevice.set("Driver", card.driver)

    secDevice.options.update(card.driver_options)

    flags = card.flags()

    for output in card.active_outputs:
        identifier = "Monitor[%s]" % output

        monSec = XorgSection("Monitor")
        parser.sections.append(monSec)
        monSec.set("Identifier", identifier)

        if card.monitors.has_key(output):
            monSec.set("VendorName",  card.monitors[output].vendor)
            monSec.set("ModelName",   card.monitors[output].model)
            monSec.set("HorizSync",   unquoted(card.monitors[output].hsync))
            monSec.set("VertRefresh", unquoted(card.monitors[output].vref ))

        if "norandr" not in flags:
            secDevice.options["Monitor-%s" % output] = identifier
            monSec.options["Enable"] = "true"

            if card.modes.has_key(output):
                monSec.options["PreferredMode"] = card.modes[output]

            if card.desktop_setup in ("horizontal", "vertical"):
                out1, out2 = card.active_outputs[:2]
                if output == out1:
                    if card.desktop_setup == "horizontal":
                        pos = "LeftOf"
                    else:
                        pos = "Above"

                    monSec.options[pos] = "Monitor[%s]" % out2

    if card.needsScreenSection():
        secScr.set("Identifier", "Screen")
        secScr.set("Device", "VideoCard")
        if card.active_outputs:
            secScr.set("Monitor", "Monitor[%s]" % card.active_outputs[0])
        secScr.set("DefaultDepth", atoi(card.depth))

        subsec = XorgSection("Display")
        subsec.set("Depth", atoi(card.depth))

        if card.needsModesLine():
            output = card.active_outputs[0]
            if card.modes.has_key(output):
                subsec.set("Modes", card.modes[output], "800x600", "640x480")

            secScr.sections = [subsec]

        secLay.set("Identifier", "Layout")
        secLay.set("Screen", "Screen")

    backup(xorgConf)

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

    device.saved_vendor_id  = cardTag.getTagData("VendorId")
    device.saved_product_id = cardTag.getTagData("ProductId")

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

    activeConfigTag = cardTag.getTag("ActiveConfig")

    driverTag = activeConfigTag.getTag("Driver")
    if driverTag:
        device.driver = driverTag.firstChild().data()
        device.package = driverTag.getAttribute("package")
    else:
        device.driver = None

    initial = activeConfigTag.getAttribute("initial")
    if initial and initial == "true":
        return device

    device.depth = activeConfigTag.getTagData("Depth")

    activeOutputs = []
    modes = {}

    def addMonitor(output, tag):
        mon = Monitor()
        mon.vendor = tag.getTagData("Vendor") or ""
        mon.model  = tag.getTagData("Model") or "Unknown Monitor"
        mon.hsync  = tag.getTagData("HorizSync") or mon.hsync
        mon.vref   = tag.getTagData("VertRefresh") or mon.vref
        device.monitors[output] = mon

    outputTag = activeConfigTag.getTag("Output")
    name = outputTag.firstChild().data()
    activeOutputs.append(name)
    mode = outputTag.getAttribute("mode")
    if mode:
        modes[name] = mode

    monitorTag = activeConfigTag.getTag("Monitor")
    if monitorTag:
        addMonitor(name, monitorTag)

    outputTag = activeConfigTag.getTag("SecondOutput")
    if outputTag:
        name = outputTag.firstChild().data()
        activeOutputs.append(name)
        mode = outputTag.getAttribute("mode")
        if mode:
            modes[name] = mode

        monitorTag = activeConfigTag.getTag("SecondMonitor")
        if monitorTag:
            addMonitor(name, monitorTag)

    device.desktop_setup = activeConfigTag.getTagData("DesktopSetup")

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

    addTag(cardTag, "VendorId", card.vendor_id)
    addTag(cardTag, "ProductId", card.product_id)

    probeResult = cardTag.insertTag("ProbeResult")
    for key, value in card.probe_result.items():
        t = probeResult.insertTag("Value")
        t.setAttribute("key", key)
        if value:
            t.insertData(value)

    config = cardTag.insertTag("ActiveConfig")

    if card.driver:
        driver = config.insertTag("Driver")
        driver.setAttribute("package", card.package)
        driver.insertData(card.driver)

    if card.initial:
        config.setAttribute("initial", "true")
    else:
        addTag(config, "Depth", card.depth)
        addTag(config, "DesktopSetup", card.desktop_setup)

        def addMonitor(output, tagName):
            mon = card.monitors[output]
            monitor = config.insertTag(tagName)
            monitor.insertTag("Vendor").insertData(mon.vendor)
            monitor.insertTag("Model" ).insertData(mon.model )
            monitor.insertTag("HorizSync"  ).insertData(mon.hsync)
            monitor.insertTag("VertRefresh").insertData(mon.vref)

        outName = card.active_outputs[0]
        outMode = card.modes.get(outName)
        output = config.insertTag("Output")
        if outMode:
            output.setAttribute("mode", outMode)
        output.insertData(outName)

        if card.monitors.has_key(outName):
            addMonitor(outName, "Monitor")

        if card.desktop_setup != "single":
            outName = card.active_outputs[1]
            outMode = card.modes.get(outName)
            output = config.insertTag("SecondOutput")
            if outMode:
                output.setAttribute("mode", outMode)
            output.insertData(outName)

            if card.monitors.has_key(outName):
                addMonitor(outName, "SecondMonitor")

    f = open(configFile, "w")
    f.write(doc.toPrettyString().replace("\n\n", ""))

    f = open(os.path.join(zorgConfigDir, "configured_card"), "w")
    f.write(info["bus-id"])

def getKeymap():
    layout = None
    variant = "basic"

    configFile = os.path.join(zorgConfigDir, zorgConfig)

    try:
        doc = piksemel.parse(configFile)

        keyboard = doc.getTag("Keyboard")
        if keyboard:
            layoutTag = keyboard.getTag("Layout")
            if layoutTag:
                layout = layoutTag.firstChild().data()

            variantTag = keyboard.getTag("Variant")
            if variantTag:
                variant = variantTag.firstChild().data()

    except OSError:
        pass

    if not layout:
        from pardus.localedata import languages

        try:
            language = file("/etc/mudur/language").read().strip()
        except IOError:
            language = "en"

        if not languages.has_key(language):
            language = "en"

        keymap = languages[language].keymaps[0]
        layout = keymap.xkb_layout
        variant = keymap.xkb_variant

    return layout, variant

def saveKeymap(layout, variant="basic"):
    if not os.path.exists(zorgConfigDir):
        os.mkdir(zorgConfigDir, 0755)

    configFile = os.path.join(zorgConfigDir, zorgConfig)

    try:
        doc = piksemel.parse(configFile)
    except OSError:
        doc = piksemel.newDocument("ZORG")

    keyboardTag = doc.getTag("Keyboard")

    if keyboardTag:
        keyboardTag.hide()

    keyboardTag = doc.insertTag("Keyboard")
    keyboardTag.insertTag("Layout").insertData(layout)
    keyboardTag.insertTag("Variant").insertData(variant)

    file(configFile, "w").write(doc.toPrettyString().replace("\n\n", ""))
