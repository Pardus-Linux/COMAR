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
#include <stddef.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <unistd.h>

#include "process.h"

#define RPC_PIPE_NAME "/tmp/comar"

struct creds {
	pid_t pid;
	uid_t uid;
	gid_t gid;
};

struct connection {
	struct connection *next, *prev;
	int sock;
	struct creds cred;
};

static int pipe_fd;
static struct connection *conns;

static int
create_pipe(const char *pipe_name)
{
	struct sockaddr_un name;
	size_t size;

	pipe_fd = socket(PF_LOCAL, SOCK_STREAM, 0);
	if (pipe_fd < 0) return -1;

	unlink(pipe_name);

	name.sun_family = AF_LOCAL;
	strncpy(name.sun_path, pipe_name, sizeof(name.sun_path));
	size = (offsetof(struct sockaddr_un, sun_path) + strlen(name.sun_path) + 1);
	if (0 != bind(pipe_fd, (struct sockaddr *) &name, size)) {
		close(pipe_fd);
		return -2;
	}

	chmod(pipe_name, 0666);

	if (0 != listen(pipe_fd, 5)) {
		close(pipe_fd);
		return -3;
	}

	return 0;
}

static int
get_peer(int sock, struct creds *cred)
{
	size_t size = sizeof(struct creds);

	// requires a linux kernel
	if (0 != getsockopt(sock, SOL_SOCKET, SO_PEERCRED, cred, &size))
		return -1;
	return 0;
}

static void
rem_conn(struct connection *c)
{
	close(c->sock);
	if (c->prev) c->prev->next = c->next;
	if (c->next) c->next->prev = c->prev;
	if (conns == c) conns = c->next;
	free(c);
}

static int
pipe_listen(void)
{
	fd_set fds;
	struct timeval tv;
	struct connection *c;
	int sock, max;
	int len;
	char buffer[1024];	// FIXME: totally lame

	tv.tv_sec = 0;
	tv.tv_usec = 0;

	FD_ZERO(&fds);
	max = 0;
	// listening pipe
	FD_SET(pipe_fd, &fds);
	if (pipe_fd > max) max = pipe_fd;
	// current connections
	for (c = conns; c; c = c->next) {
		FD_SET(c->sock, &fds);
		if (c->sock > max) max = c->sock;
	}
	++max;

	if (select(max, &fds, NULL, NULL, &tv) > 0) {
		if (FD_ISSET(pipe_fd, &fds)) {
			// new connection
			struct sockaddr_un cname;
			size_t size = sizeof(cname);
			sock = accept(pipe_fd, (struct sockaddr *)&cname, &size);
			if (sock >= 0) {
				c = calloc(1, sizeof(struct connection));
				c->sock = sock;
				if (0 == get_peer(sock, &c->cred)) {
					c->next = conns;
					c->prev = NULL;
					if (conns) conns->prev = c;
					conns = c;
				} else {
					free(c);
				}
			}
		}
		c = conns;
		while (c) {
			if (FD_ISSET(c->sock, &fds)) {
				len = recv(c->sock, buffer + 4, sizeof(buffer) - 5, 0);
				if (len <= 0) {
					struct connection *tmp;
					tmp = c->next;
					rem_conn(c);
					c = tmp;
					continue;
				}
				buffer[len + 4] = '\0';
				proc_cmd_to_parent(1, 4 + strlen(buffer) + 1);
				*(unsigned int *)&buffer[0] = (unsigned int) c;
				proc_data_to_parent(buffer, 4 + strlen(buffer) + 1);
			}
			c = c->next;
		}
	}
	return 0;
}

void
rpc_unix_start(void)
{
	struct ProcChild *p;
	struct connection *c, *t;

	if (create_pipe(RPC_PIPE_NAME) != 0) {
		puts("RPC_UNIX: Cannot create listening pipe");
		return;
	}
	printf("RPC_UNIX: listening on %s\n", RPC_PIPE_NAME);

	while (1) {
		if (1 == proc_listen(&p, 0)) {
			char *b = malloc(p->cmd.data_size);
			proc_read_data(p, b);
			c = ((struct connection **)b)[0];
			for (t = conns; t; t = t->next) {
				if (t == c) {
					send(c->sock, b + 4, p->cmd.data_size - 4, 0);
				}
			}
			free(b);
		}
		pipe_listen();
	}
}
