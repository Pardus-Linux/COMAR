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


class UserPolicy(ajan.ldaputil.LdapClass):
    entries = (
        ("mode", "comarUserSourceMode", str, None),
        ("ldap_mode", "comarUserLdapSearchMode", str, None),
        ("ldap_base", "comarUserLdapBase", str, None),
        ("ldap_filter", "comarUserLdapFilter", str, None),
    )


class Policy:
    def __init__(self):
        self.policy = UserPolicy()
    
    def update(self, computer, units):
        print "updating user policy"
        self.policy.fromEntry(computer)
    
    def apply(self):
        print "appliying user policy"
    
    def timers(self):
        return {}
