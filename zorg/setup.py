#!/usr/bin/python
#-*- coding: utf-8 -*-

import os

from distutils.core import setup, Extension
from distutils.command.install import install

import zorg

class Install(install):
    def run(self):
        install.run(self)

        if not self.root:
            self.root = "/"

        target = os.path.join(self.root, "var/lib/zorg")
        if not os.path.exists(target):
            os.makedirs(target, 0755)

setup(name="zorg",
    version=zorg.versionString(),
    description="Python Modules for zorg",
    license="GNU GPL2",
    url="http://www.pardus.org.tr/",
    packages = ["zorg"],
    ext_modules = [
        Extension("zorg.ddc",
                sources=[
                    "zorg/ddc/ddc.c",
                    "zorg/ddc/vbe.c",
                    "zorg/ddc/vesamode.c"
                ],
                libraries=["x86"]
        )
    ],
    scripts = ["zorg-cli", "inf2mondb"],
    data_files = [
        ("/usr/lib/X11", ["data/DriversDB", "data/MonitorsDB"]),
        ("/sbin", ["zorg-loadmodule"]),
        ("/etc/modprobe.d", ["data/modprobe.d/zorg"])
    ],
    cmdclass = {"install": Install}
)
