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
#include "log.h"
#include "ipc.h"

void rpc_unix_start(void);


int
main(int argc, char *argv[])
{
	struct ProcChild *p, *rpc;
	unsigned char *ipc;
	int cmd;
	int size;

	// First phase: configuration
	cfg_init(argc, argv);
	log_info("COMARd v"VERSION"\n");

	// Second phase: subsytem init
	if (db_init() != 0) return 1;
	proc_init();
	if (model_init() != 0) return 1;

	// Third phase: helper processes
	//event_start();
	rpc = proc_fork(rpc_unix_start, "RpcUnix");

	// Ready to run
	while (1) {
		if (1 == proc_listen(&p, &cmd, &size, 1)) {
			log_debug(LOG_IPC, "Main switch, cmd=%d\n", cmd);
			switch (cmd) {
				case CMD_REGISTER:
				case CMD_REMOVE:
				case CMD_CALL:
				case CMD_CALL_PACKAGE:
				case CMD_GETLIST:
					proc_recv(p, &ipc, size);
					job_start(cmd, ipc, size);
					free(ipc);
					break;
				case CMD_NOTIFY:
				case CMD_RESULT:
				case CMD_RESULT_START:
				case CMD_RESULT_END:
				case CMD_FAIL:
				case CMD_ERROR:
				case CMD_NONE:
					proc_recv(p, &ipc, size);
					proc_send(rpc, cmd, ipc, size);
					free(ipc);
					break;
			}
		}
	}

	return 0;
}
