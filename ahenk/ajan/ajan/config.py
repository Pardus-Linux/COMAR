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

import piksemel

# Constants
default_configfile = "/etc/ahenk/ajan.xml"

# Config variables
class LdapDomain:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.uri = None
        self.base_dn = None
        self.bind_dn = None
        self.bind_password = None
    
    def fromXML(self, doc):
        self.reset()
        if doc:
            self.uri = doc.getTagData("URI")
            self.base_dn = doc.getTagData("BaseDN")
            bind = doc.getTag("Bind")
            self.bind_dn = bind.getTagData("DN")
            self.bind_password = bind.getTagData("Password")


ldap = LdapDomain()

# Operations
def load():
    global ldap
    doc = piksemel.parse(default_configfile)
    ldap.fromXML(doc.getTag("Domain"))
