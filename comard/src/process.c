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
#include <signal.h>
#include <sys/wait.h>

#include "process.h"
#include "ipc.h"
#include "log.h"

struct Proc my_proc;

void
proc_init(void)
{
	memset(&my_proc, 0, sizeof(struct Proc));
	my_proc.parent.to = -1;
	my_proc.parent.from = -1;
	my_proc.desc = "MainSwitch";
	my_proc.max_children = 8;
	my_proc.children = calloc(8, sizeof(struct ProcChild));
}

static struct ProcChild *
add_child(pid_t pid, int to, int from, const char *desc)
{
	int i;

	i = my_proc.nr_children;
	if (i >= my_proc.max_children) {
		if (i == 0) {
			my_proc.max_children = 4;
		} else {
			my_proc.max_children *= 2;
		}
		my_proc.children = realloc(my_proc.children,
			my_proc.max_children * sizeof(struct ProcChild)
		);
	}
	memset(&my_proc.children[i], 0, sizeof(struct ProcChild));
	my_proc.children[i].from = from;
	my_proc.children[i].to = to;
	my_proc.children[i].pid = pid;
	my_proc.children[i].desc = desc;
	++my_proc.nr_children;
	return &my_proc.children[i];
}

static void
rem_child(int nr)
{
	int status;

	waitpid(my_proc.children[nr].pid, &status, 0);
	--my_proc.nr_children;
	if (0 == my_proc.nr_children) return;
	(my_proc.children)[nr] = (my_proc.children)[my_proc.nr_children];
}

void
proc_finish(void)
{
	exit(0);
}

struct ProcChild *
proc_fork(void (*child_func)(void), const char *desc)
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
		my_proc.parent.pid = getppid();
		my_proc.desc = desc;
		log_debug(LOG_PROC, "%s process %d started\n", desc, getpid());
		child_func();
		proc_finish();
		while (1) {} // to keep gcc happy
	} else {
		// parent process continues
		close(fdw[0]);
		close(fdr[1]);
		return add_child(pid, fdw[1], fdr[0], desc);
	}
}

int
proc_listen(struct ProcChild **senderp, int *cmdp, size_t *sizep, int timeout)
{
	unsigned int ipc;
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
			len = read(sock, &ipc, sizeof(ipc));
			*senderp = &my_proc.parent;
			*cmdp = (ipc & 0xFF000000) >> 24;
			*sizep = (ipc & 0x00FFFFFF);
			return 1;
		}
		for (i = 0; i < my_proc.nr_children; i++) {
			sock = my_proc.children[i].from;
			if (FD_ISSET(sock, &fds)) {
				len = read(sock, &ipc, sizeof(ipc));
				if (len == sizeof(ipc)) {
					*senderp = &my_proc.children[i];
					*cmdp = (ipc & 0xFF000000) >> 24;
					*sizep = (ipc & 0x00FFFFFF);
					return 1;
				} else {
					log_debug(LOG_PROC, "%s process %d finished\n",
						my_proc.children[i].desc, my_proc.children[i].pid);
					rem_child(i);
					*senderp = NULL;
					*cmdp = CMD_FINISH;
					*sizep = 0;
					return 1;
				}
			}
		}
	}
	return 0;
}

int
proc_send(struct ProcChild *p, int cmd, const void *data, size_t size)
{
	unsigned int ipc;

	if (p == TO_PARENT) p = &my_proc.parent;
	ipc = size | (cmd << 24);
	if (sizeof(cmd) != write(p->to, &ipc, sizeof(ipc))) {
		return -1;
	}
	if (size) {
		if (size != write(p->to, data, size)) {
			return -2;
		}
	}
	log_debug(LOG_IPC, "proc_send(me=%d, to=%d, cmd=%d, size=%d)\n", getpid(), p->pid, cmd, size);
	return 0;
}

int
proc_recv(struct ProcChild *p, void *datap, size_t size)
{
	char **datap2;

	datap2 = (char **) datap;
	*datap2 = malloc(size);
	if (NULL == *datap2) return -1;
	if (proc_recv_to(p, *datap2, size)) return -2;

	log_debug(LOG_IPC, "proc_recv(me=%d, from=%d, size=%d)\n", getpid(), p->pid, size);
	return 0;
}

int
proc_recv_to(struct ProcChild *p, void *data, size_t size)
{
	// FIXME: handle signals, pipe buf, etc
	if (size != read(p->from, data, size)) {
		return -1;
	}
	log_debug(LOG_IPC, "proc_recv_to(me=%d, from=%d, size=%d)\n", getpid(), p->pid, size);
	return 0;
}

char *
proc_pid_name(struct ProcChild *p)
{
	static char buf[128];

	if (p == TO_PARENT) p = &my_proc.parent;

	if (p->pid == my_proc.parent.pid)
		sprintf(buf, "parent(%d)", p->pid);
	else
		sprintf(buf, "%d", p->pid);

	return buf;
}
