#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

import comar
from dbus.mainloop.qt3 import DBusQtMainLoop

from qt import *
from kdeui import *
from kdecore import *
import dcopext


class ConnectionItem(QCustomMenuItem):
    def __init__(self, profile, pixmap):
        QCustomMenuItem.__init__(self)
        self.pixmap = pixmap
        self.text_start = self.pixmap.width() + 6

        self.menu_name = profile["name"]
        self.address_text = ""
        if " " in profile["state"]:
            self.address_text = profile["state"].split(" ", 1)[1]

    def paint(self, paint, cg, act, enabled, x, y, w, h):
        paint.setFont(self.my_font)
        fm = paint.fontMetrics()
        paint.drawPixmap(x + 3, y + (h - self.pixmap.height()) / 2, self.pixmap)
        paint.drawText(x + self.text_start, y + fm.ascent(), self.menu_name)
        paint.drawText(x + self.text_start, y + fm.height() + fm.ascent(), self.address_text)

    def sizeHint(self):
        fm = QFontMetrics(self.my_font)
        rect = fm.boundingRect(self.menu_name)
        tw, th = rect.width(), fm.height()
        if self.address_text:
            rect2 = fm.boundingRect(self.address_text)
            tw = max(tw, rect2.width())
        tw += self.text_start
        th += 3 + fm.height()
        th = max(th, self.pixmap.height() + 6)
        return QSize(tw, th)

    def setFont(self, font):
        self.my_font = QFont(font)

class NetTray(KSystemTray):
    def __init__(self, parent, link, profiles):
        KSystemTray.__init__(self)
        self.link = link
        self.parent = parent
        self.profiles = profiles
        self.popup = None
        self.menuitems = {}

        # Build menus
        self.updateMenu()

        # Listen Net.Link signals
        self.link.listenSignals("Net.Link", self.handleSignals)

        # Show yourself!
        self.updateIcon()
        self.show()

    def updateMenu(self):
        menu = self.contextMenu()
        self.parent.setMenu(menu)

    def updateIcon(self):
        state = "down"
        type_ = None

        devices = []
        for profileInfo in self.profiles:
            device_id = profileInfo["device_id"]
            package = self.parent.devices[device_id]

            if device_id not in devices:
                devices.append(device_id)

            profileName = profileInfo["name"]
            state = profileInfo["state"].split()[0]
            type_ = self.parent.info[package]["type"].split()[0]

            if state == "up":
                self.parent.updateStatus(profileName, "up")

            if state in ("up", "connecting"):
                break

        if len(devices) > 1:
            # More than one device, show "net" icon
            self.setPixmap(self.parent.getIcon("net", state))
        else:
            self.setPixmap(self.parent.getIcon(type_, state))

    def buildPopup(self):
        menu = KPopupMenu()
        self.menuitems = {}

        device = None
        for profileInfo in self.profiles:
            # Add device title if necessary
            if profileInfo["device_id"] != device:
                device = profileInfo["device_id"]
                device_name = profileInfo["device_name"].split(" - ")[0]
                menu.insertTitle(device_name)

            device_id = profileInfo["device_id"]
            package = self.parent.devices[device_id]

            type_ = self.parent.info[package]["type"].split()[0]
            state = profileInfo["state"].split()[0]

            item = ConnectionItem(profileInfo, self.parent.getIcon(type_, state))
            mid = menu.insertItem(item, -1, -1)

            self.menuitems[mid] = profileInfo

            if state in ("up", "connecting", "inaccessible"):
                menu.setItemChecked(mid, True)

            menu.connectItem(mid, self.slotSelect)

        return menu

    def slotSelect(self, mid):
        profileInfo = self.menuitems[mid]
        device_id = profileInfo["device_id"]
        package = self.parent.devices[device_id]

        profileName = profileInfo["name"]
        state = profileInfo["state"].split()[0]

        if state in ("up", "connecting"):
            self.link.Net.Link[package].setState(profileName, "down", quiet=True)
        else:
            self.link.Net.Link[package].setState(profileName, "up", quiet=True)

    def handleSignals(self, package, signal, args):
        if signal == "connectionChanged":
            action, profileName = args
            if action == "added":
                profileInfo = self.link.Net.Link[package].connectionInfo(profileName)
                self.profiles.append(profileInfo)
            elif action == "deleted":
                profile = None
                for profileInfo in self.profiles:
                    if profileInfo["name"] == profileName:
                        profile = profileInfo
                        break
                if profile:
                    self.parent.updateStatus(profileName, "down")
                    self.profiles.remove(profile)
        elif signal == "stateChanged":
            profileName, action, data = args
            for profileInfo in self.profiles:
                if profileInfo["name"] == profileName:
                    if action != "up":
                        self.parent.updateStatus(profileName, "down")
                    if len(data):
                        profileInfo["state"] = "%s %s" % (action, data)
                    else:
                        profileInfo["state"] = action
                    break
            self.buildPopup()
            self.updateIcon()

    def mousePressEvent(self, event):
        if event.button() == event.LeftButton:
            if self.popup:
                self.popup.close()
                self.popup = None
            else:
                self.popup = self.buildPopup()
                pt = self.mapToGlobal(QPoint(0, 0))
                self.popup.popup(pt)
                h = self.popup.height()
                if h + 10 > pt.y():
                    y = pt.y() + self.height()
                else:
                    y = pt.y() - h
                self.popup.move(self.popup.x(), y)
        elif event.button() == event.MidButton:
            pass
        else:
            KSystemTray.mousePressEvent(self, event)

class Applet:
    def __init__(self, app):
        self.link = comar.Link()
        self.app = app
        self.trays = []
        self.info = {}
        self.devices = {}
        self.profiles = {}
        self.profiles_up = []

        # KDE configuration
        self.config = KConfig("network-appletrc")
        self.config.setGroup("General")
        self.autoConnect = self.config.readBoolEntry("AutoConnect", True)
        self.showNotifications = self.config.readBoolEntry("ShowNotifications", True)
        self.iconPerDevice = self.config.readBoolEntry("IconPerDevice", True)
        self.notifyKDE = self.config.readBoolEntry("NotifyKDE", True)

        # Load icons
        self.loadIcons()

        # Get profiles
        self.getProfiles()

        # Build trays
        self.buildTrays()

    def getProfiles(self):
        for package in self.link.Net.Link:
            self.profiles[package] = {}
            # Get backend info
            self.info[package] = self.link.Net.Link[package].linkInfo()
            # Get device list
            for device in self.link.Net.Link[package].deviceList():
                self.devices[device] = package
            # Get profile list
            for profile in self.link.Net.Link[package].connections():
                self.profiles[package][profile] = self.link.Net.Link[package].connectionInfo(profile)

    def buildTrays(self):
        # Clear all
        for tray in self.trays:
            tray.hide()
        self.trays = []

        # Group profiles by device
        device_profiles = {}
        for package in self.profiles:
            for profile, info in self.profiles[package].iteritems():
                device = info["device_id"]
                if device not in device_profiles:
                    device_profiles[device] = []
                device_profiles[device].append(info)

        if self.iconPerDevice:
            # Crete a tray widget for each device
            for device, profileList in device_profiles.iteritems():
                tray = NetTray(self, self.link, profileList)
                self.trays.append(tray)
        else:
            profiles = []
            for device, profileList in device_profiles.iteritems():
                profiles.extend(profileList)
            tray = NetTray(self, self.link, profiles)
            self.trays.append(tray)

    def updateStatus(self, profile, status):
        if status == "up":
            if profile not in self.profiles_up:
                self.profiles_up.append(profile)
        elif status == "down":
            if profile in self.profiles_up:
                self.profiles_up.remove(profile)

        dcop = self.app.dcopClient()
        kded = dcopext.DCOPApp("kded", dcop)
        if len(self.profiles_up) > 0:
            kded.networkstatus.setNetworkStatus("COMARNetworkStatus", 8)
        else:
            kded.networkstatus.setNetworkStatus("COMARNetworkStatus", 3)

    def loadIcons(self):
        def pix(name):
            path = locate("data", "network-manager/" + name)
            img = QImage(path)
            img = img.smoothScale(24, 24)
            return QPixmap(img)

        self.iconmap = {
            "net-up": pix("ethernet-online.png"),
            "net-connecting": pix("ethernet-connecting.png"),
            "net-down": pix("ethernet-offline.png"),
            "wifi-up": pix("wireless-online.png"),
            "wifi-connecting": pix("wireless-connecting.png"),
            "wifi-down": pix("wireless-offline.png"),
            "dialup-up": pix("dialup-online.png"),
            "dialup-connecting": pix("dialup-connecting.png"),
            "dialup-down": pix("dialup-offline.png")
        }

    def getIcon(self, type_, state):
        if not type_ in ("net", "wifi", "dialup"):
            type_ = "net"
        if not state in ("up", "connecting", "down"):
            state = "down"
        return self.iconmap.get("%s-%s" % (type_, state))

    def setMenu(self, menu):
        KAction(i18n("Firewall..."), "firewall_config", KShortcut.null(), self.startFirewall, menu).plug(menu)
        KAction(i18n("Edit Connections..."), "configure", KShortcut.null(), self.startManager, menu).plug(menu)
        KAction(i18n("Connect Automatically"), "connect_creating", KShortcut.null(), self.scanAndConnect, menu).plug(menu)
        menu.insertSeparator(1)
        self.show_notify = menu.insertItem(i18n("Show Notifications"), self.setNotify, 0, -1, 1)
        menu.insertSeparator(1)
        self.device_mid = menu.insertItem(i18n("Icon Per Device"), self.deviceGroup, 0, -1, 1)
        self.single_mid = menu.insertItem(i18n("Single Icon"), self.noGroup, 0, -1, 1)

        if self.iconPerDevice:
            menu.setItemChecked(self.device_mid, True)
        else:
            menu.setItemChecked(self.single_mid, True)

        if self.showNotifications:
            menu.setItemChecked(self.show_notify, True)

        self.menu = menu

    def startFirewall(self):
        os.system("firewall-config")

    def startManager(self):
        os.system("network-manager")

    def scanAndConnect(self):
        pass

    def setNotify(self):
        if self.showNotifications:
            self.showNotifications = False
            self.config.writeEntry("ShowNotifications", False)
            menu.setItemChecked(self.show_notify, False)
        else:
            self.showNotifications = True
            self.config.writeEntry("ShowNotifications", True)
            menu.setItemChecked(self.show_notify, True)
        self.config.sync()

    def deviceGroup(self):
        self.iconPerDevice = True
        self.config.writeEntry("IconPerDevice", True)
        self.config.sync()
        self.buildTrays()

    def noGroup(self):
        self.iconPerDevice = False
        self.config.writeEntry("IconPerDevice", False)
        self.config.sync()
        self.buildTrays()


def main():
    KLocale.setMainCatalogue("network-manager")

    about = KAboutData(
        "network-applet2",
        "Network Applet",
        "0.1",
        None,
        KAboutData.License_GPL,
        "(C) 2008 UEKAE/TÜBİTAK",
        None,
        None,
        "bugs@pardus.org.tr"
    )

    # Init application
    KCmdLineArgs.init(sys.argv, about)
    KUniqueApplication.addCmdLineOptions()
    app = KUniqueApplication(True, True, True)
    app.connect(app, SIGNAL("lastWindowClosed()"), app, SLOT("quit()"))

    # Attach dbus to Qt mainloop
    DBusQtMainLoop(set_as_default=True)

    # Create applet
    applet = Applet(app)

    # Start main loop
    app.exec_loop()

if __name__ == "__main__":
    main()
