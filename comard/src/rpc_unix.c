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
#include "model.h"
#include "acl.h"

#define RPC_PIPE_NAME "/tmp/comar"

struct connection {
	struct connection *next, *prev;
	int sock;
	struct Creds cred;
	char *buffer;
	size_t size;
	int pos;
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
get_peer(int sock, struct Creds *cred)
{
	// this implementation requires a linux kernel
	struct {
		pid_t pid;
		uid_t uid;
		gid_t gid;
	} tmp;
	size_t size = sizeof(tmp);

	if (0 != getsockopt(sock, SOL_SOCKET, SO_PEERCRED, &tmp, &size))
		return -1;
	cred->uid = tmp.uid;
	cred->gid = tmp.gid;
	return 0;
}

static void
rem_conn(struct connection *c)
{
	close(c->sock);
	if (c->prev) c->prev->next = c->next;
	if (c->next) c->next->prev = c->prev;
	if (conns == c) conns = c->next;
	free(c->buffer);
	free(c);
}

static int
parse_rpc(struct connection *c)
{
	char *t, *s;
	int no;

printf("RPC [%s]\n", c->buffer);
	t = c->buffer + 1;
	switch (c->buffer[0]) {
		case '+':
			// register cmd, object name, app name, file name follows
			s = strchr(t, ' ');
			if (!s) return -1;
			*s = '\0';
			no = model_lookup_object(t);
			if (no == -1) return -1;
			t = s + 1;
			s = strchr(t, ' ');
			if (!s) return -1;
			*s = '\0';
			printf("Register node %d app %s\n", no, t);
			return 0;
		case '-':
		case '$':
		default:
			return -1;
	}
	return 0;
//		proc_send_cmd(TO_PARENT, CMD_CALL, 4 + len + 1);
//		*(unsigned int *)&buffer[0] = (unsigned int) c;
//		proc_send_data(TO_PARENT, buffer, 4 + len + 1);
}

static int
read_rpc(struct connection *c)
{
	int len;
	char *t;

	len = recv(c->sock, c->buffer + c->pos, c->size - c->pos, 0);
	if (len <= 0) return -1;

	c->buffer[c->pos + len] = '\0';
	t = strchr(c->buffer + c->pos, '\n');
	if (t) {
		*t = '\0';
		if (parse_rpc(c)) return -1;
		c->pos = 0;
	} else {
		c->pos += len;
	}
	return 0;
}

static int
pipe_listen(void)
{
	fd_set fds;
	struct timeval tv;
	struct connection *c;
	int sock, max;

	tv.tv_sec = 0;
	tv.tv_usec = 500000;

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
				c->buffer = malloc(256);
				c->size = 256;
				c->pos = 0;
				if (0 == get_peer(sock, &c->cred)) {
					c->next = conns;
					c->prev = NULL;
					if (conns) conns->prev = c;
					conns = c;
				} else {
					free(c->buffer);
					free(c);
				}
			}
		}
		c = conns;
		while (c) {
			if (FD_ISSET(c->sock, &fds)) {
				// incoming rpc data
				if (read_rpc(c)) {
					struct connection *tmp;
					tmp = c->next;
					rem_conn(c);
					c = tmp;
					continue;
				}
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
			char *b;
			if (p->cmd.cmd != CMD_RESULT) continue;
			proc_get_data(p, &b);
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
