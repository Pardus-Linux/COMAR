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
        if not line:
            return
        parts = line.split()[1:]
        # FIXME: multiple control values [...]
        self.control = parts[0]
        self.module = parts[1]
        self.args = ""
        if len(parts) > 2:
            self.args = " ".join(parts[2:])
    
    def __str__(self):
        return "%s\t%s\t%s" % (self.control, self.module, self.args)


class PamChain(list):
    def set_module(self, name, control, args="", before=None):
        self.remove_module(name)
        new_rule = PamRule()
        new_rule.module = name
        new_rule.control = control
        new_rule.args = args
        if before:
            for i, rule in enumerate(self):
                if rule.module == before:
                    self.insert(i, new_rule)
                    return
        self.insert(0, new_rule)
    
    def remove_module(self, name):
        rules =[]
        for rule in self:
            if rule.module == name:
                rules.append(rule)
        for rule in rules:
            self.remove(rule)


class PamService:
    rulesets = ("auth", "account", "password", "session")
    
    def __init__(self, filename=None):
        self.filename = filename
        
        map(lambda x: setattr(self, x, PamChain()), self.rulesets)
        
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
    
    def remove_module(self, name):
        for rulename in self.rulesets:
            chain = getattr(self, rulename)
            chain.remove_module(name)
    
    def save(self):
        f = file(self.filename, "w")
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
            service.save()
