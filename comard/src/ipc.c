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
#include "ipc.h"

struct ipc_data {
	void *chan;
	int node;
	size_t arg_len;
	char data[4];
};

static int pak_cmd;
static size_t pak_size;
static int pak_used;
static int pak_pos;
static struct ipc_data *pak_data;

void
ipc_start(int cmd, void *caller_data, int node)
{
	if (!pak_data) {
		pak_size = 256;
		pak_data = malloc(pak_size);
	}
	pak_cmd = cmd;
	pak_data->chan = caller_data;
	pak_data->node = node;
	pak_data->arg_len = 0;
	pak_used = sizeof(struct ipc_data) - 4;
}

void
ipc_pack_arg(const char *arg)
{
	pak_used += strlen(arg) + 1;
	pak_data->arg_len = strlen(arg) + 1;
	strcpy(&pak_data->data[0], arg);
}

void
ipc_pack_pair(const char *key, const char *value)
{
	size_t len;
	unsigned char *buf;

	len = strlen(key) + strlen(value) + 6;
	if (pak_used + len >= pak_size) {
		while (pak_used + len >= pak_size) {
			pak_size *= 2;
		}
		pak_data = realloc(pak_data, pak_size);
	}
	buf = (unsigned char *) pak_data;
	buf[pak_used++] = (strlen(key) + 1) & 0xFF;
	buf[pak_used++] = ((strlen(key) + 1) & 0xFF00) >> 8;
	strcpy(&buf[pak_used], key);
	pak_used += strlen(key) + 1;
	buf[pak_used++] = (strlen(value) + 1) & 0xFF;
	buf[pak_used++] = ((strlen(value) + 1) & 0xFF00) >> 8;
	strcpy(&buf[pak_used], value);
	pak_used += strlen(value) + 1;
}

void
ipc_send(struct ProcChild *p)
{
	proc_send(p, pak_cmd, pak_data, pak_used);
}

int
ipc_recv(struct ProcChild *p, size_t size)
{
	if (pak_size < size) {
		if (pak_size == 0) {
			pak_size = size;
			pak_data = malloc(size);
		} else {
			pak_size = size;
			pak_data = realloc(pak_data, size);
		}
	}

	proc_recv_to(p, pak_data, size);
	pak_pos = sizeof(struct ipc_data) - 4 + pak_data->arg_len;
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

char *
ipc_get_arg(void)
{
	if (pak_data->arg_len)
		return &pak_data->data[0];
	else
		return NULL;
}

int
ipc_get_pair(char **keyp, char **valuep)
{
	unsigned char *buf;
	int len;

	if (pak_pos >= pak_used)
		return 0;

	buf = (char *) pak_data;
	len = buf[pak_pos] + (buf[pak_pos+1] << 8);
	*keyp = buf + pak_pos + 2;
	pak_pos += 2 + len;
	len = buf[pak_pos] + (buf[pak_pos+1] << 8);
	*valuep = buf + pak_pos + 2;
	pak_pos += 2 + len;
	return 1;
}
