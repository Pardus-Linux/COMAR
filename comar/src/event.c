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
#include <unistd.h>

#include "process.h"
#include "data.h"
#include "model.h"
#include "log.h"
#include "event.h"

static struct pack *event_pak;

static int trig_node;
static char *trig_app;
static const char *trig_key;

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

//! Start the startup methods at every comar start
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

//! event process code
static void
event_proc(void)
{
	event_pak = pack_new(512);

	// First event is startup, send here when comar daemon starts
	trigger_startup_methods();

	// no more event for now, kernel device events are handled by udev
}

//! Start the event process
void
event_start(void)
{
	struct ProcChild *p;

	p = proc_fork(event_proc, "ComarEvent");
	if (!p) exit(1);
}
