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

__version__ = '2.1.1'

import dbus
import locale
import os

class Call:
    def __init__(self, link, group, class_=None, package=None, method=None):
        self.link = link
        self.group = group
        self.class_ = class_
        self.package = package
        self.method = method
        self.async = None
        self.quiet = False

        if self.package:
            self.package = self.package.replace("-", "_")

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
            packages = obj.listModelApplications("%s.%s" % (self.group, self.class_), dbus_interface=self.link.interface)
            for package in packages:
                yield unicode(package)

    def call(self, *args, **kwargs):
        self.async = kwargs.get("async", None)
        self.quiet = kwargs.get("quiet", False)
        self.timeout = kwargs.get("timeout", 120)
        if self.async and self.quiet:
            raise Exception, "async and quiet arguments can't be used together"
        if self.async or self.quiet:
            if self.package:
                obj = self.link.bus.get_object(self.link.address, "/package/%s" % self.package, introspect=False)
                met = getattr(obj, self.method)

                def handleResult(*result):
                    self.async(self.package, None, result)
                def handleError(exception):
                    if "policy.auth" in exception._dbus_error_name:
                        action = exception.get_dbus_message()
                        if self.queryPolicyKit(action):
                            return self.call(*args, **kwargs)
                    self.async(self.package, exception, None)

                if self.quiet:
                    met(dbus_interface="%s.%s.%s" % (self.link.interface, self.group, self.class_), ignore_reply=True, *args)
                else:
                    met(dbus_interface="%s.%s.%s" % (self.link.interface, self.group, self.class_), reply_handler=handleResult, error_handler=handleError, timeout=self.timeout, *args)
            else:
                def handlePackages(packages):
                    if self.quiet:
                        for package in packages:
                            obj = self.link.bus.get_object(self.link.address, "/package/%s" % package, introspect=False)
                            met = getattr(obj, self.method)
                            met(dbus_interface="%s.%s.%s" % (self.link.interface, self.group, self.class_), ignore_reply=True, *args)
                    else:
                        def handleResult(package):
                            def handler(*result):
                                return self.async(package, None, result)
                            return handler
                        def handleError(package):
                            def handler(exception):
                                return self.async(package, exception, None)
                            return handler

                        for package in packages:
                            obj = self.link.bus.get_object(self.link.address, "/package/%s" % package, introspect=False)
                            met = getattr(obj, self.method)

                            met(dbus_interface="%s.%s.%s" % (self.link.interface, self.group, self.class_), reply_handler=handleResult(package), error_handler=handleError(package), timeout=self.timeout, *args)

                def handlePackError(exception):
                    if self.quiet:
                        pass
                    else:
                        raise exception

                if self.quiet:
                    obj = self.link.bus.get_object(self.link.address, "/", introspect=False)
                    packages = obj.listModelApplications("%s.%s" % (self.group, self.class_), dbus_interface=self.link.interface)
                    handlePackages(packages)
                else:
                    obj = self.link.bus.get_object(self.link.address, "/", introspect=False)
                    obj.listModelApplications("%s.%s" % (self.group, self.class_), dbus_interface=self.link.interface, reply_handler=handlePackages, error_handler=handlePackError, timeout=self.timeout)
        else:
            if self.package:
                obj = self.link.bus.get_object(self.link.address, "/package/%s" % self.package, introspect=False)
                met = getattr(obj, self.method)
                try:
                    return met(dbus_interface="%s.%s.%s" % (self.link.interface, self.group, self.class_), timeout=self.timeout, *args)
                except dbus.DBusException, e:
                    if "policy.auth" in e._dbus_error_name:
                        action = e.get_dbus_message()
                        if self.queryPolicyKit(action):
                            return self.call(*args, **kwargs)
                    raise dbus.DBusException, e
            else:
                raise AttributeError, "Package name required for non-async calls."

    def queryPolicyKit(self, action):
        if "DISPLAY" not in os.environ:
            raise Exception, "X session required to query PolKit"
        bus = dbus.SessionBus()
        obj = bus.get_object("org.freedesktop.PolicyKit.AuthenticationAgent", "/")
        iface = dbus.Interface(obj, "org.freedesktop.PolicyKit.AuthenticationAgent")
        try:
            return iface.ObtainAuthorization(action, 0, os.getpid(), timeout=2**16-1) == 1
        except:
            return False


class Link:
    def __init__(self, version="2"):
        self.version = str(version)
        self.address = "tr.org.pardus.comar"
        self.interface = "tr.org.pardus.comar"

        self.bus = dbus.SystemBus()

        if self.version == "3":
            self.address += self.version
            self.interface += self.version

    def setLocale(self):
        if self.version != "3":
            return
        lang = locale.getdefaultlocale()[0].split("_")[0]
        obj = self.bus.get_object(self.address, '/', introspect=False)
        obj.setLocale(lang, dbus_interface=self.interface)

    def listenSignals(self, model, handler):
        def sigHandler(*args, **kwargs):
            if "/package/" not in kwargs["path"]:
                return
            package = kwargs["path"].split("/package/")[1]
            signal = kwargs["signal"]
            handler(package, signal, args)
        self.bus.add_signal_receiver(sigHandler, dbus_interface="%s.%s" % (self.interface, model), member_keyword="signal", path_keyword="path")

    def __getattr__(self, name):
        if name[0] < 'A' or name[0] > 'Z':
            raise AttributeError
        return Call(self, name)
