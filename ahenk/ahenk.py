#!/usr/bin/python
# -*- coding: utf-8 -*-
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

import comar
import SimpleXMLRPCServer

com = comar.Link()

def do_call(method, args=None):
    if args:
        com.call(method, args.split(" "))
    else:
        com.call(method)
    a = com.read_cmd()
    return a.data

rpc = SimpleXMLRPCServer.SimpleXMLRPCServer(("localhost", 8000))
rpc.register_function(do_call, "call")
rpc.serve_forever()
