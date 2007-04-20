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
import piksemel


class LdapClass:
    def fromEntry(self, attr):
        for item in self.entryDescription:
            if attr.has_key(item[1]):
                if item[2] == int:
                    val = int(attr[item[1]][0])
                elif item[2] == str:
                    val = unicode(attr[item[1]][0])
                else:
                    val = attr[item[1]]
            else:
                val = item[3]
            setattr(self, item[0], val)
    
    def toEntry(self):
        attr = {}
        for item in self.entryDescription:
            val = getattr(self, item[0])
            if item[2] == int:
                val = [str(val)]
            elif item[2] == str:
                val = [val]
            attr[item[1]] = val
        return attr


class DomainObject:
    def __init__(self, conn, dn, attr):
        self.dn = dn
        self.attr = attr
        self.name = "lala"
        if attr.has_key("cn"):
            self.name = unicode(attr["cn"][0])


class DomainComponent:
    def __init__(self, conn, dn, name):
        self.conn = conn
        self.dn = dn
        self.name = name
    
    def objects(self):
        ret = self.conn.search_s(self.dn, ldap.SCOPE_ONELEVEL, "(!(objectClass=organization))")
        kids = []
        for dn, attr in ret:
            kid = DomainObject(self.conn, dn, attr)
            kids.append(kid)
        return kids
    
    def expand(self):
        ret = self.conn.search_s(self.dn, ldap.SCOPE_ONELEVEL, "objectClass=organization")
        kids = []
        for dn, attr in ret:
            kid = DomainComponent(self.conn, dn, unicode(attr["dc"][0]))
            kids.append(kid)
        return kids


class Domain:
    def __init__(self):
        self.name = None
        self.host = None
        self.base_dn = "dc=example,dc=com"
        self.bind_dn = None
        self.bind_password = None
        
        self.conn = None
    
    def toXML(self):
        doc = piksemel.newDocument("Domain")
        doc.setAttribute("name", self.name)
        doc.insertTag("Host").insertData(self.host)
        doc.insertTag("BaseDN").insertData(self.base_dn)
        bind = doc.insertTag("Bind")
        bind.insertTag("DN").insertData(self.bind_dn)
        bind.insertTag("Password").insertData(self.bind_password)
        return doc
    
    def fromXML(self, doc):
        self.name = doc.getAttribute("name")
        self.host = doc.getTagData("Host")
        self.base_dn = doc.getTagData("BaseDN")
        bind = doc.getTag("Bind")
        self.bind_dn = bind.getTagData("DN")
        self.bind_password = bind.getTagData("Password")
    
    def connect(self):
        self.conn = ldap.open(self.host)
        self.conn.simple_bind_s(self.bind_dn, self.bind_password)
    
    def collapse(self):
        self.conn.unbind_s()
        self.conn = None
    
    def insertDC(self, name):
        if self.conn == None:
            self.connect()
        
        attr = {}
        attr["objectClass"] = ["dcObject", "organization"]
        attr["dc"] = ["example"]
        attr["o"] = ["Example Company"]
        entry = ldap.modlist.addModlist(attr)
        self.conn.add_s(self.base_dn, entry)
    
    def objects(self):
        if self.conn == None:
            self.connect()
        
        ret = self.conn.search_s(self.base_dn, ldap.SCOPE_ONELEVEL, "(!(objectClass=organization))")
        kids = []
        for dn, attr in ret:
            kid = DomainObject(self.conn, dn, attr)
            kids.append(kid)
        return kids
    
    def expand(self):
        if self.conn == None:
            self.connect()
        
        ret = self.conn.search_s(self.base_dn, ldap.SCOPE_ONELEVEL, "objectClass=organization")
        kids = []
        for dn, attr in ret:
            kid = DomainComponent(self.conn, dn, unicode(attr["dc"][0]))
            kids.append(kid)
        return kids
