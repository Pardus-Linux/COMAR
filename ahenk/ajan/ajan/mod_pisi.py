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

import threading

import ajan.ldaputil


class LocalPolicy:
    def __init__(self):
        pass
    
    def apply(self):
        pass
    
    def update_from(self, remote):
        pass
    
    def schedules(self):
        return []


class RemotePolicy(ajan.ldaputil.LdapClass):
    objectClass = "pisiPolicy"
    
    entries = (
        ("mode", "pisiAutoUpdateMode", str, "off"),
        ("interval", "pisiAutoUpdateInterval", int, 3600),
        ("repos", "pisiRepositories", str, None),
        ("zone", "pisiAutoUpdateZone", str, None),
        ("wanted", "pisiWantedPackage", list, []),
        ("unwanted", "pisiUnwantedPackage", list, []),
    )
    
    def __init__(self):
        self.fromEntry({})
    
    def parse_ou(self, attributes):
        p = Policy()
        p.fromEntry(attributes)
        self.wanted = set(self.wanted) + set(p.wanted)
        # FIXME: override
    
    def parse_computer(self, attributes):
        self.fromEntry(attributes)
