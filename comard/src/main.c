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
#include "model.h"

void job_start(void);
void rpc_unix_start(void);

int
main(int argc, char *argv[])
{
	struct ProcChild *p, *rpc;
	char *data;
	int size;

	proc_init();
	model_init();

	rpc = proc_fork(rpc_unix_start);

	while (1) {
		if (1 == proc_listen(&p, 1)) {
			printf("Child %d said %d, %d.\n", p->pid, p->cmd.cmd, p->cmd.data_size);
			if (p == rpc) {
				size = p->cmd.data_size - 4;
				proc_get_data(p, &data);
				p = proc_fork(job_start);
				p->data = ((void **)data)[0];
				proc_send_cmd(p, CMD_CALL, size);
				proc_send_data(p, data + 4, size);
				free(data);
			} else {
				switch(p->cmd.cmd) {
					case CMD_CALL:
						// another call from object
						size = p->cmd.data_size;
						proc_get_data(p, &data);
						p = proc_fork(job_start);
						p->data = NULL;
						proc_send_cmd(p, CMD_CALL, size);
						proc_send_data(p, data, size);
						free(data);
						break;
					case CMD_RESULT:
						if (p->data) {
							char *b2;
							proc_get_data(p, &data);
							b2 = malloc(4 + p->cmd.data_size);
							memcpy(b2 + 4, data, p->cmd.data_size);
							*(unsigned int *)&b2[0] = (unsigned int) p->data;
							proc_send_cmd(rpc, CMD_RESULT, p->cmd.data_size + 4);
							proc_send_data(rpc, b2, 4 + p->cmd.data_size);
						}
						break;
				}
			}
		}
//		puts("tick");
	}

	return 0;
}
