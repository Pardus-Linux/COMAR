/*
** Copyright (c) 2005-2007, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <polkit-dbus/polkit-dbus.h>

int policy_check(const char *sender, char *action, PolKitResult *result);
char *policy_action(const char *interface, const char *method);
