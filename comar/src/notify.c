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

#include "model.h"
#include "notify.h"
#include "process.h"
#include "utility.h"

//! allocate memory for notifies
void *
notify_alloc(void)
{
·   /*!
·   Allocates memory for notifies and returns pointer to allocated memory
·   Returns Null on error.
·   */

	int size;

	size = (model_max_notifications + 7)/ 8;
	return calloc(1, size);
}

//! Sets a mark if 'name' is a notify \sa model_lookup_notify
int
notify_mark(void *mask, const char *name)
{
	unsigned char *n = (unsigned char *)mask;
	int no, pos, bpos;

	no = model_lookup_notify(name);
	if (no == -1) return -1;
	pos = no / 8;
	bpos = no - (pos * 8);
	n[pos] = n[pos] | (1 << bpos);
	return 0;
}

//! Checks if notify is marked in mask
int
notify_is_marked(void *mask, int no)
{
	unsigned char *n = (unsigned char *)mask;
	int pos, bpos;

	pos = no / 8;
	bpos = no - (pos * 8);
	if (n[pos] & (1 << bpos))
		return 1;
	else
		return 0;
}

extern char *bk_app;

int
notify_fire(const char *name, const char *msg)
{
	struct ipc_struct ipc;
	struct pack *pak;
	int no;
	char *tmp;

	no = model_lookup_notify(name);
	if (no == -1) return -1;

	memset(&ipc, 0, sizeof(struct ipc_struct));
	ipc.node = no;
	pak = pack_new(256);

	if (msg) {
		tmp = malloc(strlen(msg) + strlen(bk_app) + strlen(name) + 3);
		sprintf(tmp, "%s\n%s\n%s", name, bk_app, msg);
		pack_put(pak, tmp, strlen(tmp));
		free(tmp);
	} else {
		pack_put(pak, name, strlen(name));
	}
	proc_put(TO_PARENT, CMD_NOTIFY, &ipc, pak);
	return 0;
}
