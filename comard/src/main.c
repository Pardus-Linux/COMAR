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

#include "cfg.h"
#include "process.h"
#include "model.h"
#include "data.h"
#include "job.h"
#include "rpc.h"

int
main(int argc, char *argv[])
{
	struct ProcChild *p, *rpc;
	struct reg_cmd *data;
	int cmd;
	int size;

	cfg_init(argc, argv);

	if (db_init() != 0) return 1;
	proc_init();
	if (model_init() != 0) return 1;

	rpc = proc_fork(rpc_unix_start);

	while (1) {
		if (1 == proc_listen(&p, &cmd, &size, 1)) {
			switch (cmd) {
				case CMD_REGISTER:
					proc_recv(p, &data, size);
					printf("Register(%d, %s, %s)\n", data->node, data->data, &data->data[0] + data->app_len + 1);
					job_start_register(data->node, data->data, &data->data[0] + data->app_len + 1);
					break;
				case CMD_REMOVE:
					break;
				case CMD_CALL:
					proc_recv(p, &data, size);
					printf("Call(%d)\n", data->node);
					job_start_execute(data->node, NULL);
					break;
			}
		}
//		puts("tick");
	}

	return 0;
}
