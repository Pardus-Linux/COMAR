/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - iconv.c
** charset conversion helper
*/

#include "common.h"
#include <iconv.h>

static iconv_t ic;
static int ic_ok;
static char buf[4096];

char *
my_iconv (char *text)
{
	char *in, *out;
	int in_len, out_len;

	if (!ic_ok) {
		// önce bi init edelim
		ic = iconv_open ("iso8859-9", "utf-8");
		if (ic == (iconv_t) -1) {
			fprintf (stderr, "omed: iconv init error\n");
			exit (1);
		}
		ic_ok = 1;
	}

	in = text;
	out = &buf[0];
	in_len = strlen (text);
	out_len = 4096;

	if (-1 == iconv (ic, &in, &in_len, &out, &out_len)) {
		fprintf (stderr, "omed: iconv error\n");
	}
	*out = '\0';
	return buf;
}
