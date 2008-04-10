/*
** Copyright (c) 2005-2007, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#define LOG_DBUS 1
#define LOG_PROC 2
#define LOG_PLCY 4
#define LOG_PERF 8
#define LOG_ARGS 16
#define LOG_FULL 0xffffffff

int log_start(void);
void log_error(const char *fmt, ...);
void log_info(const char *fmt, ...);
void log_debug(int subsys, const char *fmt, ...);
