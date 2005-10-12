/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#ifndef NOTIFY_H
#define NOTIFY_H 1

void *notify_alloc(void);
int notify_mark(void *mask, const char *name);
int notify_is_marked(void *mask, int no);
int notify_fire(const char *name, const char *msg);


#endif /* NOTIFY_H */
