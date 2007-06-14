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

import Queue

import ajan.config
import ajan.policy


def start():
    ajan.config.load()
    
    queue = Queue.Queue(0)
    
    policies = ajan.policy.Policies(queue)
    policies.load_default()
    policies.start_fetching()
    
    while True:
        try:
            job, data = queue.get(True, policies.next_timeout())
        except Queue.Empty:
            job , data = None, None
        
        if job is None:
            print "timeout"
            policies.start_events()
        
        elif job == "new_policy":
            print "new_policy"
            print data
            policies.update(data[0], data[1])
        
        else:
            print "error", data
            break
