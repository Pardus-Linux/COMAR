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
#include <unistd.h>

#include "process.h"
#include "ipc.h"
#include "log.h"
#include "utility.h"

struct ipc_data {
	void *chan;
	int id;
	int node;
	char data[4];
};

static int pak_cmd;
static size_t pak_size;
static int pak_used;
static int pak_pos;
static struct ipc_data *pak_data;


void
ipc_start(int cmd, void *caller_data, int id, int node)
{
	if (!pak_data) {
		pak_size = 256;
		pak_data = malloc(pak_size);
	}
	pak_cmd = cmd;
	pak_data->chan = caller_data;
	pak_data->id = id;
	pak_data->node = node;
	pak_used = sizeof(struct ipc_data) - 4;
}

void
ipc_pack_arg(const char *arg, size_t size)
{
	if (pak_used + size + 3 >= pak_size) {
		while (pak_used + size + 3 >= pak_size) {
			pak_size *= 2;
		}
		pak_data = realloc(pak_data, pak_size);
	}
	((unsigned char *)pak_data)[pak_used++] = (size & 0xff);
	((unsigned char *)pak_data)[pak_used++] = (size & 0xff00) >> 8;
	memcpy(((unsigned char *)pak_data) + pak_used, arg, size);
	pak_used += size;
	((unsigned char *)pak_data)[pak_used++] = '\0';
}

void
ipc_send(struct ProcChild *p)
{
	log_debug(LOG_IPC, "ipc_send(me=%d, to=%s, cmd=%d, size=%d)\n", getpid(), proc_pid_name(p), pak_cmd, pak_used);

	proc_send(p, pak_cmd, (unsigned char *)pak_data, pak_used);
}

int
ipc_recv(struct ProcChild *p, size_t size)
{
	log_debug(LOG_IPC, "ipc_recv(me=%d, from=%s, size=%d)\n", getpid(), proc_pid_name(p), size);

	if (pak_size < size) {
		if (pak_size == 0) {
			pak_data = malloc(size);
		} else {
			pak_data = realloc(pak_data, size);
		}
		pak_size = size;
	}

	proc_recv_to(p, pak_data, size);
	pak_pos = sizeof(struct ipc_data) - 4;
	pak_used = size;

	return 0;
}

int
ipc_get_node(void)
{
	return pak_data->node;
}

void *
ipc_get_data(void)
{
	return pak_data->chan;
}

int
ipc_get_id(void)
{
	return pak_data->id;
}

int
ipc_get_arg(char **argp, size_t *sizep)
{
	unsigned char *buf;
	size_t size;

	if (pak_pos >= pak_used) {
		*sizep = 0;
		*argp = NULL;
		return 0;
	}

	buf = (char *) pak_data;
	size = buf[pak_pos] + (buf[pak_pos+1] << 8);
	if (sizep) *sizep = size;
	if (size) *argp = buf + pak_pos + 2; else *argp = NULL;
	pak_pos += size + 2 + 1;
	return 1;
}

struct pack *
ipc_into_pack(void)
{
	struct pack *p;
	char *arg;
	size_t size;
	int pos;

	p = pack_new(pak_used);

	pos = pak_pos;
	while (ipc_get_arg(&arg, &size)) {
		pack_put(p, arg, size);
	}
	pak_pos = pos;

	return p;
}
