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
import pisi.lockeddbshelve
import pisi.ui

class UI(pisi.ui.UI):
    def confirm(self, msg):
        return True
    
    def display_progress(self, pd):
        #out = '\r%-30.30s %3d%% %12.2f %s' % \
        #    (pd['filename'], pd['percent'], pd['rate'], pd['symbol'])
        notify("System.Manager.progress", "%d" % pd['percent'])

def _init_pisi():
    ui = UI()
    try:
        pisi.api.init(ui=ui)
    except pisi.lockeddbshelve.Error, e:
        fail(str(e))

def installPackage(package=None):
    _init_pisi()
    if package:
        try:
            pisi.api.install([package])
        except pisi.packagedb.Error, e:
            return e

def removePackage(package=None):
    return "NotImplemented"

def updateIndex():
    _init_pisi()
    repos = pisi.api.ctx.repodb.list()
    if not repos:
        return "No package repository available"
    for repo in repos:
        pisi.api.update_repo(repo)
    return "Index updated"

def installCritical():
    return "NotImplemented"

def getInstalled():
    _init_pisi()
    A = pisi.packagedb.inst_packagedb.list_packages()
    A.sort()
    B = map(lambda x: "%s %s %s" % (
        x, pisi.packagedb.get_package(x).version, pisi.packagedb.get_package(x).release), A)
    return "\n".join(B)

def getUpgradable(type="all"):
    _init_pisi()
    A = pisi.api.list_upgradable()
    B = map(lambda x: "%s %s %s" % (
        x, pisi.packagedb.get_package(x).version, pisi.packagedb.get_package(x).release), A)
    return "\n".join(B)

def getPackageInfo(package=None):
    return "NotImplemented"

def getRepositories():
    _init_pisi()
    A = pisi.api.ctx.repodb.list()
    B = map(lambda x: "%s %s" % (x, pisi.api.ctx.repodb.get_repo(str(x)).indexuri.get_uri()), A)
    return "\n".join(B)

def setRepositories(repos=None):
    return "NotImplemented"
