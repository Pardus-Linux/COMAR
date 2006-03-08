#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

import os
from distutils.core import setup
from distutils.command.install import install

class Install(install):
    def finalize_options(self):
        # NOTE: for Pardus distribution
        if os.path.exists("/etc/pardus-release"):
            self.install_platlib = '$base/lib/pardus'
            self.install_purelib = '$base/lib/pardus'
        install.finalize_options(self)
    
    def run(self):
        install.run(self)

setup(
    name = 'comar',
    version = '0.1',
    description = 'COMAR API Functions',
    url = 'http://www.pardus.org.tr/projeler/comar',
    license = 'GNU GPL2',
    package_dir = { '': '' },
    packages = [ 'comar' ],
    cmdclass = {
        'install' : Install
    }
)
