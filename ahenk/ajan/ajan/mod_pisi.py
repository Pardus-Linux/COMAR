#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

import comar
import logging
import time

import ajan.ldaputil


class PisiPolicy(ajan.ldaputil.LdapClass):
    entries = (
        ("mode", "pisiAutoUpdateMode", str, None),
        ("interval", "pisiAutoUpdateInterval", int, None),
        ("repos", "pisiRepositories", str, None),
        ("zone", "pisiAutoUpdateZone", str, None),
        ("wanted", "pisiWantedPackage", list, None),
        ("unwanted", "pisiUnwantedPackage", list, None),
    )


class Policy:
    def __init__(self):
        self.policy = PisiPolicy()
        self.log = logging.getLogger("Mod.Pisi")
    
    def override(self, attr, is_ou=False):
        temp = PisiPolicy(attr)
        if is_ou:
            modes = { "off": 1, "security": 2, "full": 3 }
            if modes.get(temp.mode, 0) > modes.get(self.policy.mode, 0):
                self.policy.mode = temp.mode
            if self.policy.interval:
                if temp.interval < self.policy.interval:
                    self.policy.interval = temp.interval
            else:
                if temp.interval:
                    self.policy.interval = temp.interval
        else:
            if temp.mode:
                self.policy.mode = temp.mode
            if temp.interval:
                self.policy.interval = temp.interval
        if temp.zone:
            self.policy.zone = temp.zone
    
    def update(self, computer, units):
        self.log.debug("Updating pisi policy")
        self.policy = PisiPolicy()
        for unit in units:
            self.override(unit, True)
        self.override(computer)
        self.log.debug("Pisi policy is now:\n%s" % str(self.policy))
    
    def apply(self):
        self.log.debug("Applying pisi policy")
    
    def timers(self):
        return {
            self.autoUpdate: self.policy.interval,
        }
    
    def autoUpdate(self):
        if self.policy.zone:
            if "-" in self.policy.zone:
                # Start-End in seconds
                start, end = map(int, self.policy.zone.split("-", 1))
                temp = time.localtime()
                secs = temp.tm_hour * 60 * 60 + temp.tm_min * 60 + temp.tm_sec
                if secs < start or secs > end:
                    self.log.debug("Not in auto update zone")
                    return
        
        self.log.debug("Auto update in progress...")
        link = comar.Link()
        
        link.System.Manager["pisi"].updateAllRepositories()
        while True:
            reply = link.read_cmd()
            if reply.command != "notify":
                break
        self.log.debug("Repo update result %s" % str(reply))
        
        if reply.command != "result":
            return
        
        link.System.Manager["pisi"].updatePackage()
        while True:
            reply = link.read_cmd()
            if reply.command != "notify":
                break
        self.log.debug("Package update result %s" % str(reply))
