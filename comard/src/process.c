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

struct Proc {
	int to_parent;
	int from_parent;
	int nr_children;
	int max_children;
	int *to_children;
	int *from_children;
	pid_t *child_pids;
};

static struct Proc my_proc;

void
proc_init(void)
{
	my_proc.to_parent = -1;
	my_proc.from_parent = -1;
	my_proc.nr_children = 0;
	my_proc.max_children = 8;
	my_proc.to_children = calloc(8, sizeof(int));
	my_proc.from_children = calloc(8, sizeof(int));
	my_proc.child_pids = calloc(8, sizeof(pid_t));
}

static int
add_child(pid_t pid, int to, int from)
{
	if (my_proc.nr_children >= my_proc.max_children) {
		my_proc.max_children *= 2;
		my_proc.to_children = realloc(my_proc.to_children, my_proc.max_children * sizeof(int));
		my_proc.from_children = realloc(my_proc.from_children, my_proc.max_children * sizeof(int));
		my_proc.child_pids = realloc(my_proc.child_pids, my_proc.max_children * sizeof(pid_t));
	}
	my_proc.to_children[my_proc.nr_children] = to;
	my_proc.from_children[my_proc.nr_children] = from;
	my_proc.child_pids[my_proc.nr_children] = pid;
	++my_proc.nr_children;
	return 0;
}

static void
rem_child(int nr)
{
	--my_proc.nr_children;
	if (0 == my_proc.nr_children) return;
	my_proc.to_children[nr] = my_proc.to_children[my_proc.nr_children];
	my_proc.from_children[nr] = my_proc.from_children[my_proc.nr_children];
	my_proc.child_pids[nr] = my_proc.child_pids[my_proc.nr_children];
}

int
proc_fork(void (*child_func)(void))
{
	pid_t pid;
	int fdr[2], fdw[2];

	pipe(fdr);
	pipe(fdw);
	pid = fork();
	if (pid == -1) return -1;

	if (pid == 0) {
		// new child process starts
		close(fdw[1]);
		close(fdr[0]);
		memset(&my_proc, 0, sizeof(struct Proc));
		my_proc.from_parent = fdw[0];
		my_proc.to_parent = fdr[1];
		child_func();
		while (1) sleep(1);	// FIXME: report parent
	} else {
		// parent process continues
		close(fdw[0]);
		close(fdr[1]);
		add_child(pid, fdw[1], fdr[0]);
		return pid;
	}
}

int
proc_listen(int timeout)
{
	static char buffer[1024];	// FIXME: lame
	fd_set fds;
	struct timeval tv, *tvptr;
	int i, sock, max;

	tv.tv_sec = 0;
	tv.tv_usec = 0;

	FD_ZERO(&fds);
	if (my_proc.from_parent != -1) {
		FD_SET(my_proc.from_parent, &fds);
	}
	for (max = 0, i = 0; i < my_proc.nr_children; i++) {
		sock = my_proc.from_children[i];
		FD_SET(sock, &fds);
		if (sock > max) max = sock;
	}
	++max;
	tv.tv_sec = timeout;
	if (timeout != -1) tvptr = &tv; else tvptr = NULL;

	if (select(max, &fds, NULL, NULL, tvptr) > 0) {
		if (my_proc.from_parent != -1 && FD_ISSET(my_proc.from_parent, &fds)) {
			puts("message from parent");
		}
		for (i = 0; i < my_proc.nr_children; i++) {
			sock = my_proc.from_children[i];
			if (FD_ISSET(sock, &fds)) {
				int len;
				len = read(sock, buffer, 1023);
				buffer[len] = '\0';
				if (len > 0) {
					printf("Message from child %d: [%s]\n", my_proc.child_pids[i], buffer);
				} else {
					printf("Child %d dead\n", my_proc.child_pids[i]);
					// FIXME: handle dead child
				}
			}
		}
	}
	return 0;
}

int
proc_send_parent(const char *data, size_t size)
{
	if (0 == size) size = strlen(data);
	write(my_proc.to_parent, data, size);
	return 0;
}

void
proc_exit()
{
}
