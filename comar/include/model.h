/*
** Copyright (c) 2005-2007, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include "iksemel.h"

extern iks *model_xml;

int model_lookup_interface(const char *iface);
int model_lookup_method(const char *iface, const char *method);
char *model_get_method_access_label(int node_no);
int model_lookup_signal(const char *iface, const char *signal);
int model_get_iks(char *iface, iks **parent);
int model_init();
void model_free();
