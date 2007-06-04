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
import Queue

import ajan.config
import ajan.policy


def start():
    ajan.config.load()
    
    queue = Queue.Queue(0)
    
    t = ajan.policy.Fetcher(queue)
    t.start()
    t.join()
    
    print queue.get()
