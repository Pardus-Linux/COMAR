#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import os

class nameserver:
    def getNameServers(self, filename = "/etc/resolv.conf"):
        """ Get previously set nameservers """
        list = []

        try:
            f = file(filename, "r")
            for line in f.readlines():
                if line.strip().startswith("nameserver"):
                    list.append(line[line.find("nameserver") + 10:].rstrip('\n').strip())
            f.close()
        except IOError:
            return "Could not open file to read" # FIXME: return an error message here

        return list

    def setNameServers(self, *args):
        """ Set nameservers """
        try:
            f = file("/etc/resolv.conf", "w")
            for arg in args:
                data = "nameserver " + arg.strip() + '\n' 
                f.write(data)
            f.close()
        except IOError:
            return "Could not open file to write" # FIXME: return an error message here

        return 0

if __name__ == "__main__":
    n = nameserver()
    print n.getNameServers()
