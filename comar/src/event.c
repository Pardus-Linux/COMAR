/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#define _GNU_SOURCE 1
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

static int trig_node;
static char *trig_app;
static const char *trig_key;

static void
trig_instance(char *str, size_t size)
{
	struct pack *p;
	char *tmp, *t;
	size_t ts;

	tmp = strndup(str, size);
	p = db_get_profile(trig_node, trig_app, trig_key, tmp);

	ipc_start(CMD_CALL_PACKAGE, NULL, 0, trig_node);
	ipc_pack_arg(trig_app, strlen(trig_app));
	while (pack_get(p, &t, &ts)) {
		if (model_has_argument(trig_node, t)) {
			ipc_pack_arg(t, ts);
			pack_get(p, &t, &ts);
			ipc_pack_arg(t, ts);
		} else {
			pack_get(p, &t, &ts);
		}
	}
	ipc_send(TO_PARENT);
	pack_delete(p);
}

static void
trigger_startup_methods(void)
{
	int node;
	int flags;
	char *apps;
	const char *key;
	char *s, *t;

	// FIXME: this iterator only handles instance methods

	for (node = 0; node < model_nr_nodes; node++) {
		flags = model_flags(node);
		if ((flags & P_STARTUP) == 0)
			continue;

		key = model_instance_key(node);
		
		if (flags & P_PACKAGE) {
			if (0 != db_get_apps(model_parent(node), &apps))
				continue;
			
			for (t = apps; t; t = s) {
				s = strchr(t, '/');
				if (s) {
					*s = '\0';
					++s;
				}
				
				if (key) {
					trig_node = node;
					trig_app = t;
					trig_key = key;
				
					db_get_instances(node, t, key, trig_instance);
				}
			}

			free(apps);
		}
	}
}

static void
fire_event(const char *event, int node, const char *app, const char *data)
{
	ipc_start(CMD_EVENT, 0, 0, node);
	ipc_pack_arg(event, strlen(event));
	ipc_pack_arg(app, strlen(app));
	ipc_pack_arg(data, strlen(data));
	ipc_send(TO_PARENT);
}

static void
handle_kernel_event(const char *buffer)
{
	char *apps, *t, *s;
	int node;

	// FIXME: Net.Link is hardcoded here
	// a proper event layer must accept requests, and send
	// events to subscribers, but this is enough for 1.0 release
	// saves us to implement another db code

	printf("EVENT! [%s]\n", buffer);

	if (strncmp(buffer, "add@/class/net/", 15) == 0
		|| strncmp(buffer, "remove@/class/net/", 18) == 0) {

		node = model_lookup_class("Net.Link");

		if (db_get_apps(node, &apps) != 0)
			return;

		for (t = apps; t; t = s) {
			s = strchr(t, '/');
			if (s) {
				*s = '\0';
				++s;
			}
			fire_event("kernelEvent", node, t, buffer);
		}

		free(apps);
	}
}

static void
event_proc(void)
{
	struct sockaddr_nl snl;
	const int bufsize = 1024*1024;
	char buf[UEVENT_BUFFER_SIZE + 512];
	struct timeval tv;
	int sock;
	int ret;

	// First event is startup, send here when comar daemon starts
	trigger_startup_methods();

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
		// 1/5 sec, good for cpu and still catching shutdown signal
		tv.tv_sec = 0;
		tv.tv_usec = 200000;

		proc_check_shutdown();

		if (select(sock + 1, &fds, NULL, NULL, &tv) > 0) {
			if (FD_ISSET(sock, &fds)) {
				size_t size;
				size = recv(sock, &buf, sizeof(buf), 0);
				if (size < 0) {
					log_error("netlink recv failed.\n");
					return;
				}
				buf[size] = '\0';
				handle_kernel_event(buf);
			}
		}
	}
}

void
event_start(void)
{
	struct ProcChild *p;

	p = proc_fork(event_proc, "ComarEvent");
	if (!p) exit(1);
}
