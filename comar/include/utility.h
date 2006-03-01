/*
** Copyright (c) 2005-2006, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#ifndef UTILITY_H
#define UTILITY_H 1

#include <sys/time.h>

unsigned char *load_file(const char *fname, int *sizeptr);

int utf8_is_valid(const char *str, size_t size);

unsigned long time_diff(struct timeval *start, struct timeval *end);

struct pack {
	unsigned char *buffer;
	size_t max;
	size_t used;
	unsigned int pos;
};

struct pack *pack_new(size_t min_size);
struct pack *pack_wrap(char *buffer, size_t size);
struct pack *pack_dup(struct pack *oldpak);
void pack_delete(struct pack *p);
void pack_reset(struct pack *p);
void pack_ensure_size(struct pack *p, size_t need);
void pack_put(struct pack *p, const char *arg, size_t size);
int pack_get(struct pack *p, char **argp, size_t *sizep);
void pack_replace(struct pack *p, const char *arg, const char *value, size_t size);


#endif /* UTILITY_H */
