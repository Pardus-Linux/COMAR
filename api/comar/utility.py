#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

import os
import fcntl
import time


class FileLock:
    def __init__(self, filename):
        self.filename = filename
        self.fd = None
    
    def lock(self, shared=False, timeout=0):
        type = fcntl.LOCK_EX
        if shared:
            type = fcntl.LOCK_SH
        self.fd = os.open(self.filename, os.O_WRONLY | os.O_CREAT, 0600)
        if self.fd == -1:
            raise "Cannot create lock file"
        while True:
            try:
                fcntl.flock(self.fd, type | fcntl.LOCK_NB)
                return
            except IOError:
                if timeout > 0:
                    time.sleep(0.2)
                    timeout -= 0.2
                else:
                    os.close(self.fd)
                    raise
    
    def unlock(self):
        os.close(self.fd)
