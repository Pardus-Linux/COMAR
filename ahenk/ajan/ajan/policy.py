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

import threading

import ajan.config
import ajan.ldaputil


class Policy:
    def __init__(self):
        self.modules = {}
        for oclass, mod in ajan.config.modules.iteritems():
            self.modules[oclass] = mod.Policy()


def fetch_policy():
    conn = ajan.ldaputil.Connection()
    
    policy = Policy()
    
    # Policies of this computer
    ret = conn.search_computer()[0]
    assert(ret[0] == ajan.config.computer_dn)
    attributes = ret[1]
    
    for oc in attributes["objectClass"]:
        mod = policy.modules.get(oc, None)
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
                    mod = policy.modules.get(oc, None)
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
        except Exception, e:
            self.queue.put(("fetch_error", str(e)))
        self.queue.put(("new_policy", policy))
