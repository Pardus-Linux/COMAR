/*
** Copyright (c) 2005-2006, TUBITAK/UEKAE
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

#include "i18n.h"
#include "cfg.h"
#include "process.h"
#include "model.h"
#include "acl.h"
#include "data.h"
#include "job.h"
#include "log.h"
#include "utility.h"

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
	struct ProcChild *p;
	struct ipc_struct ipc;
	struct pack *pak;
	int cmd;
	int size;

	setlocale(LC_MESSAGES, "");
	bindtextdomain("comar", "/usr/share/locale");
	bind_textdomain_codeset("comar", "UTF-8");
	bind_textdomain_codeset("libc", "UTF-8");
	textdomain("comar");

	// First phase: configuration
	cfg_init(argc, argv);
	if (getuid() != 0) {
		puts(_("This program is a system service and should not be started by users."));
		exit(1);
	}
	proc_init(argc, argv);
	pak = pack_new(1024);
	log_start();

	// Shutdown old COMAR
	stop_running_comar();
	if (cfg_stop_only) exit(0);

	// Second phase: subsytem init
	if (db_init() != 0) return 1;
	if (model_init() != 0) return 1;
	acl_init();

	// Third phase: helper processes
	rpc_unix_start();
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
				case CMD_EVENT:
					proc_get(p, &ipc, pak, size);
					job_start(cmd, &ipc, pak);
					break;
				case CMD_CANCEL:
					proc_get(p, &ipc, pak, size);
					job_cancel(&ipc.source);
					break;
				case CMD_NOTIFY:
				case CMD_RESULT:
				case CMD_RESULT_START:
				case CMD_RESULT_END:
				case CMD_FAIL:
				case CMD_ERROR:
				case CMD_NONE:
					proc_get(p, &ipc, pak, size);
					proc_put(proc_get_rpc(), cmd, &ipc, pak);
					break;
			}
		}
	}

	return 0;
}
