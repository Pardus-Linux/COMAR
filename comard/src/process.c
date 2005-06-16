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

struct Proc my_proc;

void
proc_init(void)
{
	memset(&my_proc, 0, sizeof(struct Proc));
	my_proc.parent.to = -1;
	my_proc.parent.from = -1;
	my_proc.max_children = 8;
	my_proc.children = calloc(8, sizeof(struct ProcChild));
}

static struct ProcChild *
add_child(pid_t pid, int to, int from)
{
	int i;

	i = my_proc.nr_children;
	if (i >= my_proc.max_children) {
		my_proc.max_children *= 2;
		my_proc.children = realloc(my_proc.children,
			my_proc.max_children * sizeof(struct ProcChild)
		);
	}
	memset(&my_proc.children[i], 0, sizeof(struct ProcChild));
	my_proc.children[i].from = from;
	my_proc.children[i].to = to;
	my_proc.children[i].pid = pid;
	++my_proc.nr_children;
	return &my_proc.children[i];
}

static void
rem_child(int nr)
{
	--my_proc.nr_children;
	if (0 == my_proc.nr_children) return;
//	my_proc.to_children[nr] = my_proc.to_children[my_proc.nr_children];
}

struct ProcChild *
proc_fork(void (*child_func)(void))
{
	pid_t pid;
	int fdr[2], fdw[2];

	pipe(fdr);
	pipe(fdw);
	pid = fork();
	if (pid == -1) return NULL;

	if (pid == 0) {
		// new child process starts
		close(fdw[1]);
		close(fdr[0]);
		memset(&my_proc, 0, sizeof(struct Proc));
		my_proc.parent.from = fdw[0];
		my_proc.parent.to = fdr[1];
		child_func();
		while (1) sleep(1);	// FIXME: report parent
	} else {
		// parent process continues
		close(fdw[0]);
		close(fdr[1]);
		return add_child(pid, fdw[1], fdr[0]);
	}
}

int
proc_listen(struct ProcChild **sender, int timeout)
{
	fd_set fds;
	struct timeval tv, *tvptr;
	int i, sock, max;
	int len;

	tv.tv_sec = 0;
	tv.tv_usec = 0;

	FD_ZERO(&fds);
	max = 0;
	sock = my_proc.parent.from;
	if (sock != -1) {
		// we have a parent to listen for
		FD_SET(sock, &fds);
		if (sock > max) max = sock;
	}
	// and some children maybe?
	for (i = 0; i < my_proc.nr_children; i++) {
		sock = my_proc.children[i].from;
		FD_SET(sock, &fds);
		if (sock > max) max = sock;
	}
	++max;
	tv.tv_sec = timeout;
	if (timeout != -1) tvptr = &tv; else tvptr = NULL;

	if (select(max, &fds, NULL, NULL, tvptr) > 0) {
		sock = my_proc.parent.from;
		if (sock != -1 && FD_ISSET(sock, &fds)) {
			len = read(sock, &my_proc.parent.cmd, sizeof(struct ProcCmd));
			*sender = &my_proc.parent;
			return 1;
		}
		for (i = 0; i < my_proc.nr_children; i++) {
			sock = my_proc.children[i].from;
			if (FD_ISSET(sock, &fds)) {
				len = read(sock, &my_proc.children[i].cmd, sizeof(struct ProcCmd));
				if (len == sizeof(struct ProcCmd)) {
					*sender = &my_proc.children[i];
					return 1;
				} else {
					//printf("Child %d dead\n", my_proc.children[i].pid);
					// FIXME: handle dead child
				}
			}
		}
	}
	return 0;
}

int
proc_send_cmd(struct ProcChild *child, int cmd, unsigned int data_size)
{
	struct ProcCmd tmp;
	int to;

	if (child) to = child->to; else to = my_proc.parent.to;
	tmp.cmd = cmd;
	tmp.data_size = data_size;
	if (sizeof(struct ProcCmd) != write(to, &tmp, sizeof(struct ProcCmd))) {
		return -1;
	}
//printf("send_cmd(%d, %d)\n", cmd, data_size);
	return 0;
}

int
proc_send_data(struct ProcChild *child, const char *data, unsigned int size)
{
	int to;

	if (child) to = child->to; else to = my_proc.parent.to;
	if (0 == size) size = strlen(data);
	if (size != write(to, data, size)) {
		return -1;
	}
//printf("send_data(%d [%.*s])\n", size, size, data);
	return 0;
}

int
proc_get_data(struct ProcChild *p, char **bufferptr)
{
	size_t size;

	size = p->cmd.data_size;

	*bufferptr = malloc(size + 1);
	if (NULL == *bufferptr) return -1;
	// FIXME: try multiple times when size is bigger than pipe buf
	if (size != read(p->from, *bufferptr, size)) {
		return -2;
	}
	(*bufferptr)[size] = '\0';
//printf("get_data(%d [%.*s])\n", size, size, *bufferptr);
	return 0;
}
