/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

#include "cfg.h"
#include "log.h"

void
log_print(const char *fmt, ...)
{
	va_list ap;

	va_start(ap, fmt);

	if (cfg_log_console)
		vprintf(fmt, ap);

	if (cfg_log_file) {
		FILE *f;

		f = fopen(cfg_log_file_name, "a");
		if (f) {
			vfprintf(f, fmt, ap);
			fclose(f);
		}
	}

	// FIXME: syslog?

	va_end(ap);
}
