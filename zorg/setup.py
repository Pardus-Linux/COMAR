#!/usr/bin/python
#-*- coding: utf-8 -*-

import os

from distutils.core import setup
from distutils.command.install import install

import zorg
from zorg import consts

class Install(install):
    def run(self):
        install.run(self)

        if not self.root:
            self.root = "/"

        target = os.path.join(self.root, consts.config_dir.lstrip("/"))
        if not os.path.exists(target):
            os.makedirs(target, 0755)

setup(name="zorg",
    version=zorg.versionString(),
    description="Python Modules for zorg",
    license="GNU GPL2",
    url="http://www.pardus.org.tr/",
    packages = ["zorg"],
    scripts = ["zorg-cli", "inf2mondb"],
    data_files = [
        (consts.data_dir, ["data/DriversDB", "data/MonitorsDB"]),
        ("/sbin", ["zorg-loadmodule"]),
    ],
    cmdclass = {"install": Install}
)
