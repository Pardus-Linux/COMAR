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
    
    def update(self, computer, units):
        print "updating pisi policy"
        self.policy = PisiPolicy()
        for unit in units:
            self.override(unit, True)
        self.override(computer)
    
    def apply(self):
        print "applying pisi policy"
    
    def timers(self):
        return {
            self.autoUpdate: self.policy.interval,
        }
    
    def autoUpdate(self):
        print "auto update in progress"
        link = comar.Link()
        
        link.System.Manager["pisi"].updateAllRepositories()
        while True:
            reply = link.read_cmd()
            if reply.command != "notify":
                break
            print reply
        
        print "ur finito", reply
        
        link.System.Manager["pisi"].updatePackage()
        while True:
            reply = link.read_cmd()
            if reply.command != "notify":
                break
            print reply
        
        print "finito", reply
