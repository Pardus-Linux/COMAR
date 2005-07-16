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
#include "log.h"
#include "rpc.h"

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
	// NOTE: this implementation requires a linux kernel
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
get_str(char **str, char **arg)
{
	char *s, *t;

	s = *str;
	if (s == NULL) return -1;
	if (s[0] == '"') {
		// quoted string
		// FIXME: handle escape codes
		++s;
		*arg = s;
		t = strchr(s, '"');
		if (t) {
			*t = '\0';
			++t;
			if (t[0] == ' ') ++t;
			*str = t;
		} else {
			return -1;
		}
	} else {
		// plain string
		*arg = s;
		t = strchr(s, ' ');
		if (t) {
			*t = '\0';
			*str = t + 1;
		} else {
			*str = NULL;
		}
	}
	return 0;
}

static int
parse_rpc(struct connection *c)
{
	struct ipc_data *ipc;
	size_t size;
	char *t, *s, *s2;
	int no;

printf("RPC [%s]\n", c->buffer);
	t = c->buffer + 1;
	switch (c->buffer[0]) {
		case '+':
			// register cmd, object name, app name, file name
			if (get_str(&t, &s)) return -1;
			no = model_lookup_object(s);
			if (no == -1) return -1;
			if (get_str(&t, &s)) return -1;
			if (get_str(&t, &s2)) return -1;
			size = sizeof(struct ipc_data) + strlen(s2) + strlen(s);
			ipc = malloc(size);
			ipc->chan = (void *) c;
			ipc->node = no;
			ipc->app_len = strlen(s);
			strcpy(&ipc->data[0], s);
			strcpy(&ipc->data[0] + strlen(s) + 1, s2);
			proc_send(TO_PARENT, CMD_REGISTER, ipc, size);
			free(ipc);
			return 0;
		case '-':
			// app name
			size = sizeof(struct ipc_data) + strlen(t);
			ipc = malloc(size);
			ipc->chan = (void *) c;
			ipc->app_len = strlen(t);
			strcpy(&ipc->data[0], t);
			proc_send(TO_PARENT, CMD_REMOVE, ipc, size);
			free(ipc);
			return 0;
		case '$':
			// call cmd, method name, (app name), (args)
			no = model_lookup_method(t);
			if (no == -1) return -1;
			size = sizeof(struct ipc_data);
			ipc = malloc(size);
			ipc->chan = (void *) c;
			ipc->node = no;
			proc_send(TO_PARENT, CMD_CALL, ipc, size);
			free(ipc);
			return 0;
		default:
			return -1;
	}
	return 0;
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
	struct connection *c;
	struct ipc_data *ipc;
	int cmd;
	size_t size;

	if (create_pipe(RPC_PIPE_NAME) != 0) {
		log_print("RPC_UNIX: Cannot create listening pipe");
		return;
	}
	log_print("RPC_UNIX: listening on %s\n", RPC_PIPE_NAME);

	while (1) {
		if (1 == proc_listen(&p, &cmd, &size, 0)) {
			if (cmd != CMD_RESULT && cmd != CMD_FAIL) continue;
			proc_recv(p, &ipc, size);
			for (c = conns; c; c = c->next) {
				if (c == (struct connection *) ipc->chan) {
					send(c->sock, &ipc->data[0], ipc->app_len, 0);
				}
			}
			free(ipc);
		}
		pipe_listen();
	}
}
