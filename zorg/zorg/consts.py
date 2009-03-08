#!/usr/bin/python
# -*- coding: utf-8 -*-

xorgConf = "/etc/X11/xorg.conf"
zorgConfigDir = "/var/lib/zorg"
zorgConfig = "config.xml"
zorgDataDir = "/usr/share/zorg"

DriversDB = "%s/DriversDB" % zorgDataDir
MonitorsDB = "%s/MonitorsDB" % zorgDataDir

driver_path = "/usr/lib/xorg/modules/drivers"
xkb_path = "/usr/share/X11/xkb/symbols"

sysdir = "/sys/bus/pci/devices/"

package_sep = "/"
