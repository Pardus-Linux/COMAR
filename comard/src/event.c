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
#include <stdarg.h>
#include <sys/select.h>
#include <sys/wait.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/sysinfo.h>
#include <sys/stat.h>
#include <linux/types.h>
#include <linux/netlink.h>
#include <unistd.h>

#include "process.h"
#include "data.h"
#include "model.h"
#include "log.h"
#include "ipc.h"

#define UEVENT_BUFFER_SIZE		1024
#define NETLINK_KOBJECT_UEVENT 15


static void
event_proc(void)
{
	struct sockaddr_nl snl;
	const int bufsize = 1024*1024;
	char buf[UEVENT_BUFFER_SIZE + 512];
	int sock;
	int ret;

	memset(&snl, 0x00, sizeof(struct sockaddr_nl));
	snl.nl_family = AF_NETLINK;
	snl.nl_pid = getpid();
	snl.nl_groups = 0xffffffff;

	sock = socket(PF_NETLINK, SOCK_DGRAM, NETLINK_KOBJECT_UEVENT);
	if (sock == -1) {
		log_error("Cannot open netlink socket, event layer failed.\n");
		return;
	}

	setsockopt(sock, SOL_SOCKET, SO_RCVBUF, &bufsize, sizeof(bufsize));
	ret = bind(sock, (struct sockaddr *) &snl, sizeof(struct sockaddr_nl));
	if (ret < 0) {
		log_error("Cannot bind netlink socket, event layer failed.\n");
		return;
	}

	while (1) {
		fd_set fds;
		FD_ZERO(&fds);
		FD_SET(sock, &fds);

		if (select(sock + 1, &fds, NULL, NULL, NULL) > 0) {
			if (FD_ISSET(sock, &fds)) {
				size_t size;
				size = recv(sock, &buf, sizeof(buf), 0);
				if (size < 0) {
					log_error("netlink recv failed.\n");
					exit(1);
				}
				buf[size] = '\0';
				printf("EVENT! [%s]\n", buf);
			}
		}
	}
}

void
event_start(void)
{
	struct ProcChild *p;

	p = proc_fork(event_proc, "EventHandler");
	if (!p) exit(1);
}
