#!/usr/bin/python
# -*- coding: utf-8 -*-
import ldap
import ldap.modlist

import piksemel
import os
import sys


class Test:
    def __init__(self):
        pass
    
    def fromXML(self, doc):
        self.name = doc.getAttribute("name")
        self.host = doc.getTagData("Host")
        self.base_dn = doc.getTagData("BaseDN")
        bind = doc.getTag("Bind")
        self.bind_dn = bind.getTagData("DN")
        self.bind_password = bind.getTagData("Password")
        
    def connect(self):
        print "Connecting. Domain( %s ) " % self
        self.conn = ldap.open(self.host)
        self.conn.simple_bind_s(self.bind_dn, self.bind_password)
            
    def __str__(self):
        s = "name: %s host: %s" % (self.name, self.host) 
        return s
    
    def query(self):
        ret = self.conn.search_s(self.base_dn, ldap.SCOPE_ONELEVEL, "(!(objectClass=organization))")
        print "Query result: %s " %ret
        for dn, attr in ret:
            print "dn: %s, Attributes: %s" % (dn, attr)

if __name__ == "__main__" :
    print "hello"
    test = Test()
    path = os.path.join(os.getenv("HOME"), ".ahenk-lider.xml")
    doc = piksemel.parse(path)
    for tag in doc.getTag("Domains").tags("Domain"):
        if tag.getAttribute("name") == "local":
            print "local openldap server config read."
            test.fromXML(tag)
    print "Config: %s " % test 
    print "Connecting.."
    try:
        test.connect()
    except Exception, e:
        print "Exception: %s" % e
        print "Connection to %s failed. exiting." % test
        sys.exit()
    print "Connected successfully."
    test.query()   