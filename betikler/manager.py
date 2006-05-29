#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005,2006 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import string 

import pisi.api
import pisi.installdb
import pisi.packagedb
import pisi.lockeddbshelve
import pisi.ui
import pisi.context

class UI(pisi.ui.UI):
    def error(self, msg):
        notify("System.Manager.error","%s" % msg)

    def warning(self, msg):
        notify("System.Manager.warning","%s" % msg)

    def info(self, msg):
        notify("System.Manager.info","%s" % msg)

    def notify(self, event, **keywords):
        if event == pisi.ui.packagestogo:
            data = keywords["order"]
        else:
            data = event

        notify("System.Manager.notify","%d" % data)
        
    def ack(self, msg):
        return True
    
    def confirm(self, msg):
        return True
    
    def display_progress(self, **pd):
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
    _init_pisi()
    if package:
	try:
	    pisi.api.remove([package])
	except pisi.packagedb.Error, e:
	    return e

def updateRepository(repo=None):
    _init_pisi()
    if repo:
	try:
	    pisi.api.update_repo(repo)
	except Exception, e:
	    return e

def updateAllRepositories():
    _init_pisi()
    for repo in pisi.context.repodb.list():
	try:
	    pisi.api.update_repo(repo)
	except Exception, e:
	    return e

def addRepository(name=None,uri=None):
    _init_pisi()
    if name and uri:
	try:
	    pisi.api.add_repo(name,uri)
	except Exception, e:
	    return e

def removeRepository(repo=None):
    _init_pisi()
    if repo:
	try:
	    pisi.api.remove_repo(repo)
	except Exception, e:
	    return e

def swapRepositories(repo1=None,repo2=None):
    _init_pisi()
    if repo1 and repo2:
	try:
	    pisi.api.ctx.repodb.swap(repo1,repo2)
	except Exception, e:
	    return e

def installCritical():
    return "NotImplemented"

def getInstalled():
    _init_pisi()
    A = pisi.context.installdb.list_installed()
    A.sort(key=string.lower)
    return A

def getUpgradable(type="all"):
    _init_pisi()
    return pisi.api.list_upgradable()

def getPackageInfo(package=None):
    return "NotImplemented"

def getRepositories():
    _init_pisi()
    A = pisi.api.ctx.repodb.list()
    B = map(lambda x: "%s %s" % (x, pisi.api.ctx.repodb.get_repo(str(x)).indexuri.get_uri()), A)
    return "\n".join(B)

def setRepositories(repos=None):
    return "NotImplemented"
