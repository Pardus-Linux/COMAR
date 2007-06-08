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

import time
import threading

import ajan.config
import ajan.ldaputil


class Schedule:
    def __init__(self, interval, callable):
        self.callable = callable
        self.interval = interval
        self.last = time.time()
    
    def remaining(self, cur):
        return max(0, self.interval - (cur - self.last))
    
    def is_ready(self, cur):
        if (cur - self.last) > self.interval:
            self.last = cur
            return True
        return False


class Policies:
    def __init__(self, queue):
        self.queue = queue
        self.policies = {}
        for module in ajan.config.modules:
            self.policies[module.__name__] = module.LocalPolicy()
        self.schedules = []
        self.schedules.append(Schedule(ajan.config.policy_check_interval, self.start))
    
    def start(self):
        t = Fetcher(self.queue)
        t.start()
    
    def update_from(self, new_policies):
        for name, data in new_policies.iteritems():
            mod = self.policies.get(name, None)
            if mod:
                mod.update_from(data)
    
    def next_event_in_secs(self):
        if len(self.schedules) == 0:
            return None
        cur = time.time()
        next = min(map(lambda x: x.remaining(cur), self.schedules))
        return next
    
    def start_events(self):
        cur = time.time()
        active = filter(lambda x: x.is_ready(cur), self.schedules)
        for event in active:
            t = threading.Thread(target=event.callable)
            t.start()
        return active


class Fetcher(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.new_policies = {}
    
    def set_policy(self, oc, attributes, is_ou=False):
        for module in ajan.config.modules:
            if oc == module.RemotePolicy.objectClass:
                policy = self.new_policies.get(module.__name__, None)
                if not policy:
                    policy = module.RemotePolicy()
                    self.new_policies[module.__name__] = policy
                if is_ou:
                    policy.parse_ou(attributes)
                else:
                    policy.parse_computer(attributes)
    
    def fetch(self):
        conn = ajan.ldaputil.Connection()
        
        # Get this computer's entry
        ret = conn.search_computer()[0]
        assert(ret[0] == ajan.config.computer_dn)
        attributes = ret[1]
        
        # Organizational unit policies
        ou_list = attributes.get("ou", None)
        if ou_list:
            for unit in ou_unit:
                ret = conn.search_ou(unit)
                if len(ret) > 0:
                    attributes = ret[0][1]
                    for oc in attributes["objectClass"]:
                        self.set_policy(oc, attributes, is_ou=True)
        
        # Computer policies override OU group policies
        for oc in attributes["objectClass"]:
            self.set_policy(oc, attributes)
        
        conn.close()
        
        return self.new_policies
    
    def run(self):
        try:
            policy = self.fetch()
            self.queue.put(("new_policy", policy))
        except Exception, e:
            self.queue.put(("fetch_error", str(e)))
