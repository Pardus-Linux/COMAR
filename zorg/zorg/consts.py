#!/usr/bin/python
# -*- coding: utf-8 -*-

from os.path import join

config_dir  = "/var/lib/zorg"
data_dir    = "/usr/share/X11"
modules_dir = "/usr/lib/xorg/modules"

xorg_conf_file      = "/etc/X11/xorg.conf"
config_file         = join(config_dir,  "config.xml")
configured_bus_file = join(config_dir,  "configured_bus")
drivers_file        = join(data_dir,    "DriversDB")
monitors_file       = join(data_dir,    "MonitorsDB")
xkb_symbols_dir     = join(data_dir,    "xkb/symbols")
drivers_dir         = join(modules_dir, "drivers")

package_sep = "/"
