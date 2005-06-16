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
void rpc_unix_start(void);

int
main(int argc, char *argv[])
{
	struct ProcChild *p, *rpc;

	proc_init();

	rpc = proc_fork(rpc_unix_start);

	while (1) {
		if (1 == proc_listen(&p, 1)) {
			printf("Child %d said %d, %d.\n", p->pid, p->cmd.cmd, p->cmd.data_size);
			if (p == rpc) {
				char buf[1024]; // FIXME: totally lame
				int size = p->cmd.data_size - 4;
				proc_read_data(p, buf);
				p = proc_fork(job_start);
				proc_cmd_to_child(p, 1, size);
				proc_data_to_child(p, &buf[4], size);
			} else {
				if (p->cmd.cmd == 42) {
					// another call from object
					char buf[1024];	// FIXME: lame
					int size = p->cmd.data_size;
					proc_read_data(p, buf);
					p = proc_fork(job_start);
					proc_cmd_to_child(p, 1, size);
					proc_data_to_child(p, &buf[0], size);
				}
			}
		}
//		puts("tick");
	}

	return 0;
}
