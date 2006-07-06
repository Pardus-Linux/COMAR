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

    def notify(self, event, **keywords):
        if event == pisi.ui.downloading:
            data = "downloading"
        elif event == pisi.ui.installing:
            data = "installing"
        elif event == pisi.ui.configuring:
            data = "configuring"
        elif event == pisi.ui.extracting:
            data = "extracting"
        elif event == pisi.ui.removing:
            data = "removing"
        elif event == pisi.ui.installed:
            data = "installed"
        elif event == pisi.ui.removed:
            data = "removed"
        elif event == pisi.ui.upgraded:
            data = "upgraded"
        elif event == pisi.ui.packagestogo:
            data = ",".join(keywords["order"])
        else:
            return

        notify("System.Manager.notify","%s" % data)
        
    def ack(self, msg):
        return True
    
    def confirm(self, msg):
        return True
    
    def display_progress(self, **pd):
        out = "%s,%d,%d,%s,%d,%d" % (pd["filename"],pd['percent'],pd["rate"],pd["symbol"],pd["downloaded_size"],pd["total_size"])
        notify("System.Manager.progress", out)

def _init_pisi():
    ui = UI()
    try:
        pisi.api.init(ui=ui)
    except pisi.lockeddbshelve.Error, e:
        notify("System.Manager.error","%s" % str(e))

def finished():
    notify("System.Manager.finished","")
    
def installPackage(package=None):
    _init_pisi()
    if package:
        try:
            package = package.split(",")
            pisi.api.install(package)
        except Exception,e:
            fail(unicode(e))
    finished()

def updatePackage(package=None):
    _init_pisi()
    if package:
        try:
            package = package.split(",")
            pisi.api.upgrade(package)
        except Exception,e:
            fail(unicode(e))
    finished()
                                                            
def removePackage(package=None):
    _init_pisi()
    if package:
	try:
            package = package.split(",")
            pisi.api.remove(package)
	except Exception, e:
	    fail(unicode(e))
    finished()

def updateRepository(repo=None):
    _init_pisi()
    if repo:
	try:
            notify("System.Manager.updatingRepo","%s" % repo)
	    pisi.api.update_repo(repo)
	except Exception, e:
	    fail(unicode(e))
    finished()

def updateAllRepositories():
    _init_pisi()
    for repo in pisi.context.repodb.list():
	try:
            notify("System.Manager.updatingRepo","%s" % repo)
	    pisi.api.update_repo(repo)
	except Exception, e:
	    fail(unicode(e))
    finished()

def addRepository(name=None,uri=None):
    _init_pisi()
    if name and uri:
	try:
	    pisi.api.add_repo(name,uri)
	except Exception, e:
	    fail(unicode(e))
    finished()

def removeRepository(repo=None):
    _init_pisi()
    if repo:
	try:
	    pisi.api.remove_repo(repo)
	except Exception, e:
	    fail(unicode(e))
    finished()

def swapRepositories(repo1=None,repo2=None):
    _init_pisi()
    if repo1 and repo2:
	try:
	    pisi.api.ctx.repodb.swap(repo1,repo2)
	except Exception, e:
            fail(unicode(e))
    finished()

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
