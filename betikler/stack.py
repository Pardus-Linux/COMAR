#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

import os
import re
import string

rc_path = "/etc/resolv.conf"
name_path = "/etc/conf.d/hostname"
hosts_path = "/etc/hosts"
env_cmd = "/usr/bin/update-environ.py"
host_cmd = "/usr/bin/hostname %s"
valid_name_chars = string.ascii_letters + string.digits + '.' + '_' + '-'

def getNameServers():
    f = file(rc_path)
    list = [ x.split(" ", 1)[1].rstrip("\n") for x in f.readlines() if x.startswith("nameserver ") ]
    return "\n".join(list)

def setNameServers(nameservers=None):
    f = file(rc_path)
    list = filter(lambda x: not "nameserver" in x, f.readlines())
    f.close()
    servers = map(lambda x: "nameserver %s\n" % x, nameservers.split("\n"))
    f = file(rc_path, "w")
    f.write("".join(list) + "".join(servers))
    f.close()

def getHostNames():
    dict = get_profile("Net.Stack.setHostNames")
    if dict and dict.has_key("hostnames"):
        return dict["hostnames"]
    return ""

def setHostNames(hostnames=None):
    if not hostnames:
        return
    invalid = filter(lambda x: not x in valid_name_chars, hostnames)
    if len(invalid) > 0:
        fail("Invalid characters '%s' in hostname" % ("".join(invalid)))
    
    # hostname
    f = file(name_path)
    data = f.read()
    f.close()
    data = re.sub('HOSTNAME="(.*)"', 'HOSTNAME="%s"' % hostnames, data)
    f = file(name_path, "w")
    f.write(data)
    f.close()
    
    # hosts
    f = file(hosts_path)
    data = f.readlines()
    f.close()
    f = file(hosts_path, "w")
    flag = 1
    for line in data:
        if line.startswith("127.0.0.1"):
            line = "127.0.0.1 localhost %s\n" % hostnames
            flag = 0
        f.write(line)
    if flag:
        f.write("127.0.0.1 localhost %s\n" % hostnames)
    f.close()
    
    # update environment
    os.system(env_cmd)
    
    # we dont call the following command, it mess up system
    # hostname changes take effect after restart
    #os.system(host_cmd % hostnames)
