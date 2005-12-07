/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#ifndef UTILITY_H
#define UTILITY_H 1

struct pack {
	unsigned char *buffer;
	size_t max;
	size_t used;
	unsigned int pos;
};

struct pack *pack_new(size_t min_size);
struct pack *pack_wrap(char *buffer, size_t size);
void pack_delete(struct pack *p);
void pack_ensure_size(struct pack *p, size_t need);
void pack_put(struct pack *p, const char *arg, size_t size);
int pack_get(struct pack *p, char **argp, size_t *sizep);
void pack_replace(struct pack *p, const char *arg, const char *value, size_t size);


#endif /* UTILITY_H */
