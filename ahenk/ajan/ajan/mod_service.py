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
import ajan.ldaputil


class ServicePolicy(ajan.ldaputil.LdapClass):
    """ Service policy class has 2 attributes : service names to start, service names to stop """    
    entries = (
        ("start", "comarServiceStart", set, set()),
        ("stop", "comarServiceStop", set, set()),
    )


class Policy:
    def __init__(self):
        self.policy = ServicePolicy()
        self.log = logging.getLogger("Mod.Service")
    
    def override(self, attr, is_ou = False):
        """ Overrides service policy"""
        temp = ServicePolicy(attr)
        
        # Retrieve current service policy
        start_set = temp.start
        stop_set = temp.stop
        
        if is_ou:
            start_set.union(self.policy.start)
            stop_set.union(self.policy.stop)
        
        else:
            start_set = start_set.union(self.policy.start)
            start_set = start_set.difference(stop_set)
            
            stop_set = stop_set.union(self.policy.stop)
            stop_set = stop_set.difference(start_set)
        
        self.policy.start = start_set
        self.policy.stop = stop_set
    
    def update(self, computer, units):
        """ Updates service policy"""
        self.log.debug("Updating Service Policy")
        self.policy = ServicePolicy()
        for unit in units:
            self.override(unit, True)
        self.override(computer)
        self.log.debug("Service policy is now:\n%s" % str(self.policy))
    
    def apply(self):
        self.log.debug("Applying Service Policy" )
        link = comar.Link()
        
        def serviceSetState(service, state):
            link.System.Service[service].setState(state=state)
            link.read_cmd()
        
        def serviceStart(service):
            link.System.Service[service].start()
            link.read_cmd()
        
        def serviceStop(service):
            link.System.Service[service].stop()
            link.read_cmd()
        
        for service in self.policy.stop:
            serviceSetState(service, "off")
            serviceStop(service)
        
        for service in self.policy.start:
            serviceSetState(service, "on")
            serviceStart(service)
