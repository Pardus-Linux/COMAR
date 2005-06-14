/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#ifndef PROCESS_H
#define PROCESS_H 1

void proc_init(void);
int proc_fork(void (*child_func)(void));
int proc_listen(int timeout);
int proc_send_parent(const char *data, size_t size);


#endif /* PROCESS_H */
