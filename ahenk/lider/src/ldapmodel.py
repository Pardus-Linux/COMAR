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

import ldap
import ldap.modlist


class DomainComponent:
    def __init__(self, name):
        self.name = name


class Domain:
    def __init__(self, name):
        self.name = name
        
        self.host = "127.0.0.1"
        self.bind_dn = "cn=Manager,dc=example,dc=com"
        self.bind_password = "*****"
        self.conn = None
    
    def connect(self):
        self.conn = ldap.open(self.host)
        self.conn.simple_bind_s(self.bind_dn, self.bind_password)
    
    def insertDC(self, name):
        if self.conn == None:
            self.connect()
        
        attr = {}
        attr["objectClass"] = ["dcObject", "organization"]
        attr["dc"] = ["example"]
        attr["o"] = ["Example Company"]
        entry = ldap.modlist.addModlist(attr)
        self.conn.add_s("dc=example,dc=com", entry)
    
    def expand(self):
        if self.conn == None:
            self.connect()
        
        return [DomainComponent("Pardus"), DomainComponent("Optik")]
