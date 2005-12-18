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
#include <stddef.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <unistd.h>

#include "cfg.h"
#include "process.h"
#include "model.h"
#include "data.h"
#include "job.h"
#include "log.h"
#include "ipc.h"

void rpc_unix_start(void);
void event_start(void);


static void
stop_running_comar(void)
{
	const char check[] = { 42, 0, 0, 0, 0, 0, 0, 0 };
	char buf[100];
	struct sockaddr_un name;
	size_t size;
	int sock;

	sock = socket(PF_LOCAL, SOCK_STREAM, 0);
	if (sock == -1) return;

	name.sun_family = AF_LOCAL;
	strncpy(name.sun_path, cfg_socket_name, sizeof (name.sun_path));
	size = (offsetof (struct sockaddr_un, sun_path) + strlen (name.sun_path) + 1);
	if (connect(sock, (struct sockaddr *) &name, size) != 0) {
		// no old comar running, continue with initialization
		close(sock);
		return;
	}

	log_info("Stopping old COMAR...\n");

	// send retirement check
	write(sock, &check, sizeof(check));

	while (1) {
		int len;
		len = read(sock, &buf, sizeof(buf));
		if (len <= 0) break;
	}
}

int
main(int argc, char *argv[])
{
	struct ProcChild *p, *rpc;
	unsigned char *ipc;
	int cmd;
	int size;

	// First phase: configuration
	cfg_init(argc, argv);
	log_info("COMAR v"VERSION"\n");

	// Shutdown old COMAR
	stop_running_comar();
	if (cfg_stop_only) exit(0);

	// Second phase: subsytem init
	if (db_init() != 0) return 1;
	proc_init();
	if (model_init() != 0) return 1;

	// Third phase: helper processes
	rpc = proc_fork(rpc_unix_start, "RpcUnix");
	event_start();

	// Ready to run
	while (1) {
		if (1 == proc_listen(&p, &cmd, &size, 1)) {
			log_debug(LOG_IPC, "Main switch, cmd=%d\n", cmd);
			switch (cmd) {
				case CMD_SHUTDOWN:
					// our job here is finished, leave the building
					log_info("Shutdown requested.\n");
					proc_finish();
					break;
				case CMD_REGISTER:
				case CMD_REMOVE:
				case CMD_CALL:
				case CMD_CALL_PACKAGE:
				case CMD_GETLIST:
				case CMD_DUMP_PROFILE:
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
					proc_send(proc_get_rpc(), cmd, ipc, size);
					free(ipc);
					break;
			}
		}
	}

	return 0;
}
