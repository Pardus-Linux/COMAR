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

#include "process.h"

void job_start(void);

static char *funcs[] = {
	"funcA",
	"funcB",
	"funcC"
};

int
main(int argc, char *argv[])
{
	struct ProcChild *p;
	int i;

	proc_init();

	for (i = 0; i < 16; i++) {
		p = proc_fork(job_start);
		proc_cmd_to_child(p, 1, 5);
		proc_data_to_child(p, funcs[i % 3], 5);
	}

	while (1) {
		if (1 == proc_listen(&p, 1)) {
			printf("Child %d said %d, %d.\n", p->pid, p->cmd.cmd, p->cmd.data_size);
		}
//		puts("tick");
	}

	return 0;
}
