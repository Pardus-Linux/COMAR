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

import sys
import getopt

import ajan.main

def usage():
    print "usage: ahenk-ajan [--debug]"

def main(args):
    debug = False
    
    try:
        opts, args = getopt.getopt(args, "d", ["debug"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    
    for opt, val in opts:
        if opt in ("-d", "--debug"):
            debug = True
    
    ajan.main.start(debug=debug)

if __name__ == "__main__":
    main(sys.argv[1:])
