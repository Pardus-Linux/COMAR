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

header = "#%PAM-1.0\n\n"


class PamRule:
    def __init__(self, line=None):
        parts = line.split()[1:]
        # FIXME: multiple control values [...]
        self.control = parts[0]
        self.module = parts[1]
        self.args = ""
        if len(parts) > 2:
            self.args = " ".join(parts[2:])
    
    def __str__(self):
        return "%s\t%s\t%s" % (self.control, self.module, self.args)


class PamService:
    rulesets = ("auth", "account", "password", "session")
    
    def __init__(self, filename=None):
        map(lambda x: setattr(self, x, []), self.rulesets)
        
        if filename:
            part = ""
            for line in file(filename):
                line = line.strip()
                if line and not line.startswith("#"):
                    if line.endswith("\\"):
                        part = part + line[:-1]
                    else:
                        line = part + line
                        rule = PamRule(line)
                        type_, rest = line.split(None, 1)
                        rules = getattr(self, type_)
                        rules.append(rule)
                        part = ""
    
    def __str__(self):
        temp = ""
        for rulename in self.rulesets:
            for rule in getattr(self, rulename):
                temp += "%s\t%s\n" % (rulename, str(rule))
            temp += "\n"
        return temp
    
    def save(self, filename):
        f = file(filename, "w")
        f.write(header)
        f.write(str(self))
        f.close()


class Pam:
    pam_d = "/etc/pam.d"
    
    def __init__(self):
        self.services = {}
    
    def load(self):
        for name in os.listdir(self.pam_d):
            self.services[name] = PamService(os.path.join(self.pam_d, name))
    
    def save(self):
        for name, service in self.services.iteritems():
            service.save(os.path.join(self.pam_d, name))
            service.save(name)
