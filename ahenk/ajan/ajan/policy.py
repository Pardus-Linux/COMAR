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
        return self.interval - (cur - self.last)
    
    def is_ready(self, cur):
        if (cur - self.last) > self.interval:
            self.last = cur
            return True
        return False


class Policy:
    def __init__(self):
        self.schedules = []
        self.policies = {}
        for oclass, mod in ajan.config.modules.iteritems():
            self.policies[oclass] = mod.Policy()
    
    def next_event_in_secs(self):
        if len(self.schedules) == 0:
            return None
        cur = time.time()
        next = min(map(lambda x: x.remaining(cur), self.schedules))
        return next
    
    def events(self):
        cur = time.time()
        active = filter(lambda x: x.is_ready(cur), self.schedules)
        return active


def fetch_policy():
    conn = ajan.ldaputil.Connection()
    
    policy = Policy()
    
    # Policies of this computer
    ret = conn.search_computer()[0]
    assert(ret[0] == ajan.config.computer_dn)
    attributes = ret[1]
    
    for oc in attributes["objectClass"]:
        mod = policy.policies.get(oc, None)
        if mod:
            mod.parse(attributes)
    
    # Organizational unit policies
    ou_list = attributes.get("ou", None)
    if ou_list:
        for unit in ou_unit:
            ret = conn.search_ou(unit)
            if len(ret) > 0:
                attributes = ret[0][1]
                for oc in attributes["objectClass"]:
                    mod = policy.policies.get(oc, None)
                    if mod:
                        mod.parse_ou(attributes)
    
    conn.close()
    
    return policy


class Fetcher(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
    
    def run(self):
        try:
            policy = fetch_policy()
            self.queue.put(("new_policy", policy))
        except Exception, e:
            self.queue.put(("fetch_error", str(e)))
