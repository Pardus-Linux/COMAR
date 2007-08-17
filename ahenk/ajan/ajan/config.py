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

import mod_pisi
import mod_user
import mod_service

# Constant file names
default_configfile = "/etc/ahenk/ajan.xml"
default_policyfile = "/etc/ahenk/current-policy.ldif"

# Configuration variables
class LdapDomain:
    	
    def __init__(self):
	    
        """ Default vaues for 'uri', 'base_dn', 'bind_dn' and 'bind_password' attributes """
        self.uri = None
        self.base_dn = None
        self.bind_dn = None
        self.bind_password = None
    
    def fromXML(self, doc):
        """ Retrieves LdapDomain object's attributes' values from an XML partion """
        
        if doc:
            self.uri = doc.getTagData("URI")
            self.base_dn = doc.getTagData("BaseDN")
            bind = doc.getTag("Bind")
            if bind:
                self.bind_dn = bind.getTagData("DN")
                self.bind_password = bind.getTagData("Password")

ldap = LdapDomain()

computer_dn = None

policy_check_interval = 4 * 60

# modele names tuple : #
modules = (
    mod_pisi,
    mod_user,
    mod_service,
)

# Operations
def load():
    """ parses default configuration file -/etc/ahenk/ajan.xml- 
    	Reads "Domain" tagged part and retrieves values for 'ldap's attrıbutes, 'computer_dn' and 'policy_check_interval' variables
    """
    global ldap
    global computer_dn
    global policy_check_interval
    doc = piksemel.parse(default_configfile)
    ldap.fromXML(doc.getTag("Domain"))
    computer_dn = doc.getTagData("ComputerDN")
    interval = doc.getTagData("PolicyCheckInterval")
    if interval:
        policy_check_interval = int(interval)
