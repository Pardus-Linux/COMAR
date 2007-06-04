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

def fetch_policy():
    conn = ajan.ldaputil.Connection()
    
    # This computer
    ret = conn.search_computer()[0]
    assert(ret[0] == ajan.config.computer_dn)
    attributes = ret[1]
    
    for oc in attributes["objectClass"]:
        mod = ajan.config.modules.get(oc, None)
        if mod:
            mod.parse_policy(None, attributes)
    
    conn.close()


class Fetcher(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
    
    def run(self):
        fetch_policy()
        self.queue.put("result")
