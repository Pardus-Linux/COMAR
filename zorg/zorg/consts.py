#!/usr/bin/python
# -*- coding: utf-8 -*-

xorgConf = "/etc/X11/xorg.conf"
zorgConfigDir = "/var/lib/zorg"
zorgConfig = "config.xml"

DriversDB = "/usr/lib/X11/DriversDB"
MonitorsDB = "/usr/lib/X11/MonitorsDB"

driver_path = "/usr/lib/xorg/modules/drivers"
xkb_path = "/usr/share/X11/xkb/symbols"

sysdir = "/sys/bus/pci/devices/"

lcd_drivers = ["nv", "nvidia", "ati", "via", "i810",
               "intel", "sis", "savage", "neomagic"]
truecolor_cards = ["i810", "intel", "nv", "radeon"]

package_sep = "/"
