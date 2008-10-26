#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

__version__ = '2.1.0'

import dbus

class Call:
    def __init__(self, link, group, class_=None, package=None, method=None):
        self.link = link
        self.group = group
        self.class_ = class_
        self.package = package
        self.method = method
        self.async = None
        self.quiet = False

    def __getitem__(self, key):
        if not self.class_:
            raise KeyError, "Package should be selected after class"
        if not isinstance(key, basestring):
            raise KeyError
        return Call(self.link, self.group, self.class_, key)

    def __getattr__(self, name):
        if self.class_:
            c = Call(self.link, self.group, self.class_, self.package, name)
            return c.call
        else:
            if name[0] < 'A' or name[0] > 'Z':
                raise AttributeError

            return Call(self.link, self.group, name)

    def __iter__(self):
        if self.class_:
            obj = self.link.bus.get_object(self.link.address, "/", introspect=False)
            packages = obj.listModelApplications("%s.%s" % (self.group, self.class_), dbus_interface="tr.org.pardus.comar")
            for package in packages:
                yield unicode(package)

    def call(self, *args, **kwargs):
        self.async = kwargs.get("async", None)
        self.quiet = kwargs.get("quiet", False)
        if self.async and self.quiet:
            raise Exception, "async and quiet arguments can't be used together"
        if self.async or self.quiet:
            if self.package:
                obj = self.link.bus.get_object(self.link.address, "/package/%s" % self.package, introspect=False)
                met = getattr(obj, self.method)

                def handleResult(*result):
                    self.async(self.package, None, result)
                def handleError(exception):
                    self.async(self.package, exception, None)

                if self.quiet:
                    met(dbus_interface="tr.org.pardus.comar.%s.%s" % (self.group, self.class_), ignore_reply=True, *args)
                else:
                    met(dbus_interface="tr.org.pardus.comar.%s.%s" % (self.group, self.class_), reply_handler=handleResult, error_handler=handleError, *args)
            else:
                def handlePackages(packages):
                    for package in packages:
                        obj = self.link.bus.get_object(self.link.address, "/package/%s" % package, introspect=False)
                        met = getattr(obj, self.method)

                        if self.quiet:
                            met(dbus_interface="tr.org.pardus.comar.%s.%s" % (self.group, self.class_), ignore_reply=True, *args)
                        else:
                            def handleResult(*result):
                                self.async(package, None, result)
                            def handleError(exception):
                                self.async(package, exception, None)

                            met(dbus_interface="tr.org.pardus.comar.%s.%s" % (self.group, self.class_), reply_handler=handleResult, error_handler=handleError, *args)

                def handlePackError(exception):
                    if self.quiet:
                        pass
                    else:
                        raise exception

                if self.quiet:
                    obj = self.link.bus.get_object(self.link.address, "/", introspect=False)
                    packages = obj.listModelApplications("%s.%s" % (self.group, self.class_), dbus_interface="tr.org.pardus.comar")
                    handlePackages(packages)
                else:
                    obj = self.link.bus.get_object(self.link.address, "/", introspect=False)
                    obj.listModelApplications("%s.%s" % (self.group, self.class_), dbus_interface="tr.org.pardus.comar", reply_handler=handlePackages, error_handler=handlePackError)
        else:
            if self.package:
                obj = self.link.bus.get_object(self.link.address, "/package/%s" % self.package, introspect=False)
                met = getattr(obj, self.method)
                return met(dbus_interface="tr.org.pardus.comar.%s.%s" % (self.group, self.class_), *args)
            else:
                raise AttributeError, "Package name required for non-async calls."


class Link:
    def __init__(self, address="tr.org.pardus.comar"):
        self.address = address
        self.bus = dbus.SystemBus()

    def __getattr__(self, name):
        if name[0] < 'A' or name[0] > 'Z':
            raise AttributeError
        return Call(self, name)
