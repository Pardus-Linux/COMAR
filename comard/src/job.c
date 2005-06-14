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
#include <sys/stat.h>

#include "csl.h"
#include "process.h"

static unsigned char *
load_file(const char *fname, int *sizeptr)
{
	FILE *f;
	struct stat fs;
	size_t size;
	unsigned char *data;

	if (stat (fname, &fs) != 0) {
		printf ("Cannot stat file '%s'\n", fname);
		exit (2);
	}
	size = fs.st_size;
	if (sizeptr) *sizeptr = size;

	data = malloc (size + 1);
	if (!data) {
		printf ("Cannot allocate %d bytes\n", size);
		exit (2);
	}
	memset(data, 0, size + 1);

	f = fopen (fname, "rb");
	if (!f) {
		printf ("Cannot open file '%s'\n", fname);
		exit (2);
	}

	if (fread (data, size, 1, f) < 1) {
		printf ("Read error in file '%s'\n", fname);
		exit (2);
	}

	fclose (f);
	return data;
}

void
job_start(void)
{
	char *buf;
	char *code;
	size_t codelen;
	int e;

	csl_setup();

	buf = load_file("test.py", NULL);
	e = csl_compile(buf, "test", &code, &codelen);
	if (e) {
		proc_send_parent("compile error", 0);
		exit(1);
	}

	e = csl_execute(code, codelen, "funcA");
	if (e) {
		proc_send_parent("execute error", 0);
		exit(4);
	}

	proc_send_parent("OK", 2);

	csl_cleanup();
}
