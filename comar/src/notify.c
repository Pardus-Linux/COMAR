/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <stdlib.h>
#include <string.h>

#include "model.h"
#include "notify.h"
#include "process.h"
#include "ipc.h"

void *
notify_alloc(void)
{
	int size;

	size = (model_max_notifications + 7)/ 8;
	return calloc(1, size);
}

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

int
notify_fire(const char *name, const char *msg)
{
	int no;

	no = model_lookup_notify(name);
	if (no == -1) return -1;
	ipc_start(CMD_NOTIFY, NULL, 0, no);
	if (msg) ipc_pack_arg(msg, strlen(msg));
	ipc_send(TO_PARENT);
	return 0;
}
