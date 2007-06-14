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
    
    def update(self, computer, units):
        print "updating pisi policy"
        self.policy.fromEntry(computer)
    
    def apply(self):
        print "applying pisi policy"
    
    def timers(self):
        return {
            self.autoUpdate: self.policy.interval,
        }
    
    def autoUpdate(self):
        print "auto update in progress"
