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
import Queue
import threading
import StringIO
import logging
import ldif
import sha

import ajan.config
import ajan.ldaputil


class Timer:
    
    """ Timer class : attribute 'last' refreshes its value to system time in a period of 'interval' attribute's value """	

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


class Applier(threading.Thread):

    """      """
    
    def __init__(self, apply_queue, result_queue):
	    
	"""  """
        threading.Thread.__init__(self)
        self.log = logging.getLogger("Applier")
        self.apply_queue = apply_queue
        self.result_queue = result_queue
	
	#Create all modules' -module names are stored in a tuple in config.py file- Policy objects and stores them in 'policies' list 
        self.policies = map(lambda x: x.Policy(), ajan.config.modules)
        self.timers = {}
    
    def next_timeout(self):
	
	""" Returns nearest next_timeout of the timers """
	
        if len(self.timers) == 0:
            return None
        cur = time.time()
        next = min(map(lambda x: x.remaining(cur), self.timers.values()))
        next = max(1, next)
        return next
    
    def update_policy(self, policy, computer, units):
	
	""" Updates policy in the modules : calls 'update' and 'apply' functions of each policy   """
	
        self.log.debug("Updating %s", policy.__module__)
        
        try:
	    # 'update' function updates policy attributes, 'apply' functions does the related actions
	    	
            policy.update(computer, units)
            policy.apply()
	    
        except Exception, e:
            self.result_queue.put(("error", str(e)))
            return
	
        #If there exists timers attribute in the policy : ???????????????????
        func = getattr(policy, "timers", None)
        if func:
            for callable, interval in func().iteritems():
                if interval and interval != 0:
                    old = self.timers.get(callable, None)
                    if old:
                        old.interval = interval
                    else:
                        self.timers[callable] = Timer(interval, callable)
                else:
                    if self.timers.get(callable, None):
                        del self.timers[callable]
    
    def run(self):
        """ ?????????????????????????????????????"""
	
	self.log.debug("started")
        
        while True:
            try:
                new_policy = self.apply_queue.get(True, self.next_timeout())
            except Queue.Empty:
                new_policy = None
            
            if new_policy:
                computer, units = new_policy
                for policy in self.policies:
                    self.update_policy(policy, computer, units)
            else:
                cur = time.time()
                active = filter(lambda x: x.is_ready(cur), self.timers.values())
                for event in active:
                    try:
                        event.callable()
                    except Exception, e:
                        self.result_queue.put(("error", str(e)))


#
#
#


class Loader(ldif.LDIFParser):
    def handle(self, dn, attr):
        if self.comp:
            self.ou.append(attr)
        else:
            self.comp = attr


class Fetcher(threading.Thread):
    
    """   """
    
    def __init__(self, result_queue):
        threading.Thread.__init__(self)
        self.result_queue = result_queue
        self.log = logging.getLogger("Fetcher")
    
    def fetch(self):
        self.log.debug("Fetching new policy...")
        
        conn = ajan.ldaputil.Connection()
        
        policy_output = StringIO.StringIO()
        output = ldif.LDIFWriter(policy_output)
        
        # Get this computer's entry
        ret = conn.search_computer()[0]
        comp_attr = ret[1]
        output.unparse(ret[0], ret[1])
        
        # Organizational unit policies
        ou_attrs = []
        ou_list = comp_attr.get("ou", [])
        for unit in ou_list:
            ret = conn.search_ou(unit)
            if len(ret) > 0:
                ret = ret[0]
                output.unparse(ret[0], ret[1])
                ou_attrs.append(ret[1])
        
        conn.close()
        
        policy_ldif = policy_output.getvalue()
        policy_output.close()
        
        # Save a copy of fetched policy
        f = file(ajan.config.default_policyfile, "w")
        f.write(policy_ldif)
        f.close()
        
        return comp_attr, ou_attrs, sha.sha(policy_ldif).hexdigest()
    
    def run(self):
        self.log.debug("started")
        
        old_hash = None
        
        # Load latest fetched policy if available
        if os.path.exists(ajan.config.default_policyfile):
            self.log.debug("Loading old policy...")
            old_hash = sha.sha(file(ajan.config.default_policyfile).read()).hexdigest()
            
            loader = Loader(file(ajan.config.default_policyfile))
            loader.comp = None
            loader.ou = []
            loader.parse()
            
            if loader.comp:
                message = "policy", (loader.comp, loader.ou)
                self.result_queue.put(message)
        
        # Periodically fetch latest policy
        while True:
            try:
                computer, units, ldif_hash = self.fetch()
                if ldif_hash != old_hash:
                    self.log.debug("Policy has changed")
                    message = "policy", (computer, units)
                    self.result_queue.put(message)
                    old_hash = ldif_hash
                else:
                    self.log.debug("Policy is still same")
            except Exception, e:
                self.result_queue.put(("error", "Fetch error: %s" % str(e)))
            
            time.sleep(ajan.config.policy_check_interval)
