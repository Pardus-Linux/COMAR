/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#include "utility.h"

struct pack *
pack_new(size_t min_size)
{
	struct pack *p;

	p = calloc(sizeof(struct pack), 1);
	if (!p) return NULL;
	if (min_size < 256) min_size = 256;
	p->max = min_size;
	p->buffer = malloc(p->max);
	if (!p->buffer) {
		free(p);
		return NULL;
	}
	return p;
}

struct pack *
pack_wrap(char *buffer, size_t size)
{
	struct pack *p;

	p = calloc(sizeof(struct pack), 1);
	if (!p) return NULL;
	p->buffer = buffer;
	p->max = size;
	p->used = size;
	return p;
}

void
pack_delete(struct pack *p)
{
	free(p->buffer);
	free(p);
}

void
pack_ensure_size(struct pack *p, size_t need)
{
	if (need >= p->max) {
		while (need >= p->max) p->max *= 2;
		p->buffer = realloc(p->buffer, p->max);
	}
}

void
pack_put(struct pack *p, const char *arg, size_t size)
{
	unsigned char *ptr;
	size_t need;

	need = p->used + size + 3;
	pack_ensure_size(p, need);

	ptr = p->buffer + p->used;
	*ptr++ = (size & 0xff);
	*ptr++ = (size & 0xff00) >> 8;
	memcpy(ptr, arg, size);
	ptr += size;
	*ptr = '\0';

	p->used += size + 3;
}

int
pack_get(struct pack *p, char **argp, size_t *sizep)
{
	unsigned char *ptr;
	size_t size;

	if (p->pos >= p->used) {
		*sizep = 0;
		*argp = NULL;
		return 0;
	}

	ptr = p->buffer + p->pos;
	size = ptr[0] + (ptr[1] << 8);
	if (sizep) *sizep = size;
	if (size) *argp = ptr + 2; else *argp = NULL;
	p->pos += 2 + size + 1;

	return 1;
}

void
pack_replace(struct pack *p, const char *arg, const char *value, size_t size)
{
	char *t;
	size_t ts;

	p->pos = 0;
	while (pack_get(p, &t, &ts)) {
		if (strcmp(t, arg) == 0) {
			// found it, replace the old value
			return;
		}
		// skip the argument's value
		pack_get(p, &t, &ts);
	}
	// no old value, append as new
	pack_put(p, arg, strlen(arg));
	pack_put(p, value, size);
}
