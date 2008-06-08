/*
** Copyright (c) 2005-2007, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <Python.h>
#include <dbus/dbus.h>

void dbus_send(DBusMessage *reply);
void dbus_signal(const char *path, const char *interface, const char *name, PyObject *obj);
void dbus_method_call(DBusMessage* msg, DBusConnection* conn);
void dbus_listen();
void dbus_app_methods(const char *interface, const char *path, const char *method);
char *dbus_caller_locale(DBusMessage *msg);
