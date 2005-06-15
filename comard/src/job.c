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
	struct ProcChild *sender;
	char *buf;
	char *code;
	char func[128];
	size_t codelen;
	int e;

	while (1) {
		if (1 == proc_listen(&sender, 1)) break;
	}
	proc_read_data(sender, &func[0]);
	func[sender->cmd.data_size] = '\0';

	csl_setup();

	buf = load_file("test.py", NULL);
	e = csl_compile(buf, "test", &code, &codelen);
	if (e) {
		proc_cmd_to_parent(-1, 0);
		exit(1);
	}

	e = csl_execute(code, codelen, func);
	if (e) {
		proc_cmd_to_parent(-1, 0);
		exit(4);
	}

	proc_cmd_to_parent(1, 0);

	csl_cleanup();
}
