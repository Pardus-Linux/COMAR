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


class Timer:
    def __init__(self, interval, callable):
        self.interval = interval
        self.callable = callable
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
        self.policies = map(lambda x: x.Policy(), ajan.config.modules)
        self.timers = {}
        self.timers[self.start_fetching] = \
            Timer(ajan.config.policy_check_interval, self.start_fetching)
    
    def update(self, computer, units):
        for policy in self.policies:
            policy.update(computer, units)
        for callable, interval in policy.timers().iteritems():
            if interval and interval != 0:
                old = self.timers.get(callable, None)
                if old:
                    old.interval = interval
                else:
                    self.timers[callable] = Timer(interval, callable)
            else:
                if self.timers[callable]:
                    del self.timers[callable]
        # FIXME: start applying
    
    def next_timeout(self):
        if len(self.timers) == 0:
            return None
        cur = time.time()
        next = min(map(lambda x: x.remaining(cur), self.timers.values()))
        next = max(0.5, next)
        return next
    
    def start_events(self):
        cur = time.time()
        active = filter(lambda x: x.is_ready(cur), self.timers.values())
        for event in active:
            t = threading.Thread(target=event.callable)
            t.start()
    
    def start_fetching(self):
        print "fetching new policy..."
        t = Fetcher(self.queue)
        t.start()


class Fetcher(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
    
    def fetch(self):
        conn = ajan.ldaputil.Connection()
        
        # Get this computer's entry
        ret = conn.search_computer()[0]
        assert(ret[0] == ajan.config.computer_dn)
        comp_attr = ret[1]
        
        # Organizational unit policies
        ou_attrs = []
        ou_list = comp_attr.get("ou", None)
        if ou_list:
            for unit in ou_unit:
                ret = conn.search_ou(unit)
                if len(ret) > 0:
                    ou_attrs.append(ret[0][1])
        
        conn.close()
        
        return comp_attr, ou_attrs
    
    def run(self):
        try:
            policy = self.fetch()
            self.queue.put(("new_policy", policy))
        except Exception, e:
            self.queue.put(("fetch_error", str(e)))
