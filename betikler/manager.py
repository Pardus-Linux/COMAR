#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import pisi.api
import pisi.installdb
import pisi.packagedb

def installPackage(package=None):
    pisi.api.init()
    if package:
        pisi.api.install(package)

def removePackage(package=None):
    return "NotImplemented"

def updateIndex():
    pisi.api.init()
    repos = pisi.api.ctx.repodb.list()
    if not repos:
        return "No package repository available"
    for repo in repos:
        pisi.api.update_repo(repo)
    return "Index updated"

def installCritical():
    return "NotImplemented"

def getInstalled():
    pisi.api.init()
    A = pisi.packagedb.inst_packagedb.list_packages()
    A.sort()
    B = map(lambda x: "%s %s %s" % (
        x, pisi.packagedb.get_package(x).version, pisi.packagedb.get_package(x).release), A)
    return "\n".join(B)

def getUpgradable(type="all"):
    pisi.api.init()
    A = pisi.api.list_upgradable()
    B = map(lambda x: "%s %s %s" % (
        x, pisi.packagedb.get_package(x).version, pisi.packagedb.get_package(x).release), A)
    return "\n".join(B)
