/*
** Copyright (c) 2005-2006, TUBITAK/UEKAE
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

#define UEVENT_BUFFER_SIZE 1024
#define NETLINK_KOBJECT_UEVENT 15

#include "process.h"
#include "data.h"
#include "model.h"
#include "log.h"
#include "event.h"

struct event_hook {
	struct event_hook *next;
	char *filter;
	int class;
	char *function;
	char *app;
};

static struct event_hook *event_table[EVENT_MAX];

static struct pack *event_pak;

static int trig_node;
static char *trig_app;
static const char *trig_key;

static void
add_hook(int type, char *filter, int class, char *function, char *app)
{
	struct event_hook *hook;

	hook = calloc(1, sizeof(struct event_hook));
	if (!hook) return;
	hook->filter = strdup(filter);
	if (!hook->filter) {
		free(hook);
		return;
	}
	hook->class = class;
	hook->function = strdup(function);
	if (!hook->function) {
		free(hook->filter);
		free(hook);
		return;
	}
	hook->app = strdup(app);
	if (!hook->app) {
		free(hook->function);
		free(hook->filter);
		free(hook);
		return;
	}

	hook->next = event_table[type];
	event_table[type] = hook;
}

static void
fire_event(const char *function, int class, const char *app, const char *data)
{
	struct ipc_struct ipc;

	memset(&ipc, 0, sizeof(struct ipc_struct));
	ipc.node = class;
	pack_reset(event_pak);
	pack_put(event_pak, function, strlen(function));
	pack_put(event_pak, app, strlen(app));
	pack_put(event_pak, data, strlen(data));
	proc_put(TO_PARENT, CMD_EVENT, &ipc, event_pak);
}

static void
fire_kernel_events(const char *buffer)
{
	struct event_hook *hook;

	for (hook = event_table[EVENT_KERNEL]; hook; hook = hook->next) {
		if (strncmp(buffer, hook->filter, strlen(hook->filter)) == 0) {
			fire_event(hook->function, hook->class, hook->app, buffer);
		}
	}
}

static void
trig_instance(char *str, size_t size)
{
	struct ipc_struct ipc;
	struct pack *p;
	char *tmp, *t;
	size_t ts;

	memset(&ipc, 0, sizeof(struct ipc_struct));

	tmp = strndup(str, size);
	p = db_get_profile(trig_node, trig_app, trig_key, tmp);

	ipc.node = trig_node;
	pack_reset(event_pak);
	pack_put(event_pak, trig_app, strlen(trig_app));
	while (pack_get(p, &t, &ts)) {
		if (model_has_argument(trig_node, t)) {
			pack_put(event_pak, t, ts);
			pack_get(p, &t, &ts);
			pack_put(event_pak, t, ts);
		} else {
			pack_get(p, &t, &ts);
		}
	}
	proc_put(TO_PARENT, CMD_CALL_PACKAGE, &ipc, event_pak);
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
event_proc(void)
{
	struct sockaddr_nl snl;
	const int bufsize = 1024*1024;
	char buf[UEVENT_BUFFER_SIZE + 512];
	struct timeval tv;
	int sock;
	int ret;

	event_pak = pack_new(512);

	// FIXME: load from db
	add_hook(EVENT_KERNEL, "add@/class/net", model_lookup_class("Net.Link"), "kernelEvent", "net-tools");
	add_hook(EVENT_KERNEL, "remove@/class/net", model_lookup_class("Net.Link"), "kernelEvent", "net-tools");
	add_hook(EVENT_KERNEL, "add@/class/net", model_lookup_class("Net.Link"), "kernelEvent", "wireless-tools");
	add_hook(EVENT_KERNEL, "remove@/class/net", model_lookup_class("Net.Link"), "kernelEvent", "wireless-tools");

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
				fire_kernel_events(buf);
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
