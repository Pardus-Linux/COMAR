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

import os
import time
import threading
import StringIO
import ldif
import sha

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


class Loader(ldif.LDIFParser):
    def handle(self, dn, attr):
        if self.comp:
            self.ou.append(attr)
        else:
            self.comp = attr


class Policies:
    def __init__(self, queue):
        self.queue = queue
        self.old_hash = None
        self.policies = map(lambda x: x.Policy(), ajan.config.modules)
        self.timers = {}
        self.timers[self.start_fetching] = \
            Timer(ajan.config.policy_check_interval, self.start_fetching)
    
    def load_default(self):
        if not os.path.exists(ajan.config.default_policyfile):
            return
        
        loader = Loader(file(ajan.config.default_policyfile))
        loader.comp = None
        loader.ou = []
        loader.parse()
        
        if loader.comp:
            self.update((loader.comp, loader.ou, None))
    
    def update(self, data):
        computer, units, ldif_hash = data
        if ldif_hash is not None:
            if ldif_hash == self.old_hash:
                print "policy hasnt changed"
                return
        self.old_hash = ldif_hash
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
        # FIXME: one thread per job
        for policy in self.policies:
            t = threading.Thread(target=policy.apply)
            t.start()
    
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
        
        policy_output = StringIO.StringIO()
        output = ldif.LDIFWriter(policy_output)
        
        # Get this computer's entry
        ret = conn.search_computer()[0]
        assert(ret[0] == ajan.config.computer_dn)
        comp_attr = ret[1]
        output.unparse(ret[0], ret[1])
        
        # Organizational unit policies
        ou_attrs = []
        ou_list = comp_attr.get("ou", None)
        if ou_list:
            for unit in ou_unit:
                ret = conn.search_ou(unit)
                if len(ret) > 0:
                    output.unparse(ret[0], ret[1])
                    ou_attrs.append(ret[0][1])
        
        conn.close()
        
        policy_ldif = policy_output.getvalue()
        policy_output.close()
        
        f = file(ajan.config.default_policyfile, "w")
        f.write(policy_ldif)
        f.close()
        
        return comp_attr, ou_attrs, sha.sha(policy_ldif).digest()
    
    def run(self):
        try:
            policy = self.fetch()
            self.queue.put(("new_policy", policy))
        except Exception, e:
            self.queue.put(("fetch_error", str(e)))
