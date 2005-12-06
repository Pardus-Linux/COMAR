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
#include "cfg.h"
#include "ipc.h"
#include "notify.h"

/* rpc commands, keep in sync with bindings */
enum {
	// outgoing
	RPC_RESULT = 0,
	RPC_FAIL,
	RPC_NONE,
	RPC_DENIED,
	RPC_ERROR,
	RPC_RESULT_START,
	RPC_RESULT_END,
	RPC_NOTIFY,
	// incoming
	RPC_LOCALIZE,
	RPC_REGISTER,
	RPC_REMOVE,
	RPC_CALL,
	RPC_CALL_PACKAGE,
	RPC_ASKNOTIFY,
	RPC_GETLIST,
	RPC_CHECKACL,
	RPC_DUMP_PROFILE
};

#define RPC_SHUTDOWN 42

struct connection {
	struct connection *next, *prev;
	int sock;
	struct Creds cred;
	void *notify_mask;
	char *buffer;
	size_t size;
	size_t data_size;
	int pos;
};

static int pipe_fd;
static struct connection *conns;

// unpack utilities
// rpc uses network byte order (big endian)
static inline unsigned int
get_cmd(const unsigned char *buf)
{
	return buf[0];
}

static inline unsigned int
get_data_size(const unsigned char *buf)
{
	return buf[3] + (buf[2] << 8) + (buf[1] << 16);
}

static inline unsigned int
get_id(const unsigned char *buf)
{
	return buf[3] + (buf[2] << 8) + (buf[1] << 16) + (buf[0] << 24);
}

static inline unsigned int
get_size(const unsigned char *buf)
{
	return buf[1] + (buf[0] << 8);
}


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

struct arg_s {
	unsigned char *buffer;
	size_t size;
	int pos;
};

int
get_arg(struct arg_s *args, char **argp, size_t *sizep)
{
	size_t size;

	if (args->pos == args->size)
		// no more arguments
		return 0;

	if (args->pos + 2 >= args->size)
		return -1;

	size = get_size(args->buffer + args->pos);
	args->pos += 2;
	if (args->pos + size >= args->size) return -1;
	*sizep = size;
	*argp = args->buffer + args->pos;
	// FIXME: validate utf8
	args->pos += size;
	if (args->buffer[args->pos] != '\0') return -1;
	++args->pos;
	return 1;
}

static int
write_rpc(struct connection *c, unsigned int cmd, int id, const char *buffer, size_t size)
{
	unsigned char head[8];

	head[4] = (id >> 24) & 0xFF;
	head[5] = (id >> 16) & 0xFF;
	head[6] = (id >> 8) & 0xFF;
	head[7] = id & 0xFF;

	if (RPC_RESULT == cmd) {
		char *s;
		size_t sz;

		ipc_get_arg(&s, &sz);
//printf("writeRPC(%d,%d,%d,%s,%d,%s)\n", cmd, id, sz, s, size, buffer);

		head[0] = cmd & 0xFF;
		head[1] = ((size + 1 + sz) >> 16) & 0xFF;
		head[2] = ((size + 1 + sz) >> 8) & 0xFF;
		head[3] = (size + 1 + sz) & 0xFF;
		send(c->sock, head, 8, 0);
		send(c->sock, buffer, size, 0);
		send(c->sock, " ", 1, 0);
		send(c->sock, s, sz, 0);
		return 0;
	}

//printf("writeRPC(%d,%d,%d,%s)\n", cmd, id, size, buffer);
	head[0] = cmd & 0xFF;
	head[1] = (size >> 16) & 0xFF;
	head[2] = (size >> 8) & 0xFF;
	head[3] = size & 0xFF;
	send(c->sock, head, 8, 0);
	if (size) send(c->sock, buffer, size, 0);

	return 0;
}

static int
parse_rpc(struct connection *c)
{
	struct arg_s args;
	int cmd, id, no;
	char *t;
	size_t sz;

	cmd = get_cmd(c->buffer);
	id = get_id(c->buffer + 4);

//printf("RPC cmd %d, id %d, size %d\n", cmd, id, c->data_size);

	args.buffer = c->buffer + 8;
	args.pos = 0;
	args.size = c->data_size;

	switch (cmd) {
		case RPC_SHUTDOWN:
			// no parameter
			if (!acl_is_capable(CMD_SHUTDOWN, 0, &c->cred)) return -1;
			write_rpc(c, RPC_RESULT, id, NULL, 0);
			ipc_start(CMD_SHUTDOWN, 0, 0, 0);
			ipc_send(TO_PARENT);
			return 0;

		case RPC_REGISTER:
			// class name, package name, file name
			if (get_arg(&args, &t, &sz) != 1) return -1;
			no = model_lookup_class(t);
			if (no == -1) return -1;
			if (!acl_is_capable(CMD_REGISTER, no, &c->cred)) return -1;
			ipc_start(CMD_REGISTER, (void *)c, id, no);
			if (get_arg(&args, &t, &sz) != 1) return -1;
			ipc_pack_arg(t, sz);
			if (get_arg(&args, &t, &sz) != 1) return -1;
			ipc_pack_arg(t, sz);
			if (get_arg(&args, &t, &sz) != 0) return -1;
			ipc_send(TO_PARENT);
			return 0;

		case RPC_REMOVE:
			// package name
			if (!acl_is_capable(CMD_REMOVE, 0, &c->cred)) return -1;
			if (get_arg(&args, &t, &sz) != 1) return -1;
			ipc_start(CMD_REMOVE, (void *)c, id, 0);
			ipc_pack_arg(t, sz);
			if (get_arg(&args, &t, &sz) != 0) return -1;
			ipc_send(TO_PARENT);
			return 0;

		case RPC_CHECKACL:
			// method name
			if (get_arg(&args, &t, &sz) != 1) return -1;
			no = model_lookup_method(t);
			if (no == -1) return -1;
			if (!acl_is_capable(CMD_CALL, no, &c->cred)) {
				write_rpc(c, RPC_DENIED, id, NULL, 0);
			} else {
				write_rpc(c, RPC_RESULT, id, NULL, 0);
			}
			return 0;

		case RPC_CALL:
			// method name, arg pairs (key-value)
			if (get_arg(&args, &t, &sz) != 1) return -1;
			no = model_lookup_method(t);
			if (no == -1) return -1;
			if (!acl_is_capable(CMD_CALL, no, &c->cred)) {
				write_rpc(c, RPC_DENIED, id, NULL, 0);
				return 0;
			}
			ipc_start(CMD_CALL, (void *)c, id, no);
			while (1) {
				int ret = get_arg(&args, &t, &sz);
				if (ret == 0) break;
				if (ret == -1) return -1;
				if (!model_has_argument(no,  t)) return -1;
				ipc_pack_arg(t, sz);
				if (get_arg(&args, &t, &sz) != 1) return -1;
				ipc_pack_arg(t, sz);
			}
			ipc_send(TO_PARENT);
			return 0;

		case RPC_CALL_PACKAGE:
			// method name, package name, arg pairs (key-value)
			if (get_arg(&args, &t, &sz) != 1) return -1;
			no = model_lookup_method(t);
			if (no == -1) return -1;
			if (!acl_is_capable(CMD_CALL, no, &c->cred)) {
				write_rpc(c, RPC_DENIED, id, NULL, 0);
				return 0;
			}
			ipc_start(CMD_CALL_PACKAGE, (void *)c, id, no);
			if (get_arg(&args, &t, &sz) != 1) return -1;
			ipc_pack_arg(t, sz);
			while (1) {
				int ret = get_arg(&args, &t, &sz);
				if (ret == 0) break;
				if (ret == -1) return -1;
				if (!model_has_argument(no,  t)) return -1;
				ipc_pack_arg(t, sz);
				if (get_arg(&args, &t, &sz) != 1) return -1;
				ipc_pack_arg(t, sz);
			}
			ipc_send(TO_PARENT);
			return 0;

		case RPC_GETLIST:
			// class name
			if (get_arg(&args, &t, &sz) != 1) return -1;
			no = model_lookup_class(t);
			if (no == -1) return -1;
			if (!acl_is_capable(CMD_CALL, no, &c->cred)) {
				write_rpc(c, RPC_DENIED, id, NULL, 0);
				return 0;
			}
			ipc_start(CMD_GETLIST, (void *)c, id, no);
			ipc_send(TO_PARENT);
			return 0;

		case RPC_ASKNOTIFY:
			// notify name
			if (get_arg(&args, &t, &sz) != 1) return -1;
			if (notify_mark(c->notify_mask, t) != 0) return -1;
			return 0;

		case RPC_DUMP_PROFILE:
			// no parameter
			if (!acl_is_capable(CMD_DUMP_PROFILE, 0, &c->cred)) return -1;
			ipc_start(CMD_DUMP_PROFILE, (void *)c, id, 0);
			ipc_send(TO_PARENT);
			return 0;

		default:
			return -1;
	}
}

static int
read_rpc(struct connection *c)
{
	int len;

	if (c->pos < 8) len = 8 - c->pos; else len = c->data_size + 8 - c->pos;
	len = recv(c->sock, c->buffer + c->pos, len, 0);
	if (len <= 0) return -1;

	c->pos += len;
	if (c->pos >= 8) {
		c->data_size = get_data_size(c->buffer);
	}
	if (c->pos == c->data_size + 8) {
		if (parse_rpc(c)) return -1;
		c->data_size = 0;
		c->pos = 0;
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
	tv.tv_usec = 250000;

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
				c->notify_mask = notify_alloc();
				c->buffer = malloc(256);
				c->size = 256;
				if (0 == get_peer(sock, &c->cred)) {
					c->next = conns;
					c->prev = NULL;
					if (conns) conns->prev = c;
					conns = c;
				} else {
					free(c->buffer);
					free(c);
					close(sock);
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
forward_reply(struct ProcChild *p, size_t size, int cmd)
{
	struct connection *c;
	char *s;
	size_t sz;

	ipc_recv(p, size);
	for (c = conns; c; c = c->next) {
		if (c == (struct connection *) ipc_get_data()) {
			ipc_get_arg(&s, &sz);
			write_rpc(c, cmd, ipc_get_id(), s, sz);
			return;
		}
	}
}

void
rpc_unix_start(void)
{
	struct ProcChild *p;
	struct connection *c;
	int cmd;
	size_t size;
	char *s;
	size_t sz;

	if (create_pipe(cfg_socket_name) != 0) {
		log_error("RPC_UNIX: Cannot create listening pipe '%s'\n", cfg_socket_name);
		return;
	}
	log_info("RPC_UNIX: listening on %s\n", cfg_socket_name);

	while (1) {
		while (1 == proc_listen(&p, &cmd, &size, 0)) {
			switch (cmd) {
				case CMD_NOTIFY:
					ipc_recv(p, size);
					ipc_get_arg(&s, &sz);
					for (c = conns; c; c = c->next) {
						int no = ipc_get_node();
						if (notify_is_marked(c->notify_mask, no)) {
							write_rpc(c, RPC_NOTIFY, 0, s, sz);
						}
					}
					continue;
				case CMD_RESULT_START:
					forward_reply(p, size, RPC_RESULT_START);
					break;
				case CMD_RESULT_END:
					forward_reply(p, size, RPC_RESULT_END);
					break;
				case CMD_RESULT:
					forward_reply(p, size, RPC_RESULT);
					break;
				case CMD_FAIL:
					forward_reply(p, size, RPC_FAIL);
					break;
				case CMD_ERROR:
					forward_reply(p, size, RPC_ERROR);
					break;
				case CMD_NONE:
					forward_reply(p, size, RPC_NONE);
					break;
				default:
					// this shouldn't happen, warn and skip
					log_error("RPC: Unexpected internal command %d\n", cmd);
					ipc_recv(p, size);
			}
		}
		pipe_listen();
	}
}
