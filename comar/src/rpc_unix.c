/*
** Copyright (c) 2005-2006, TUBITAK/UEKAE
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
#include "notify.h"

//! rpc commands, keep in sync with bindings
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
	RPC_DUMP_PROFILE,
	RPC_CANCEL,
	RPC_EVENT
};

#define RPC_SHUTDOWN 42

static int comar_shutting_down = 0;

struct connection {
	struct connection *next, *prev;
	unsigned int cookie;
	int sock;
	struct Creds cred;
	void *notify_mask;
	char *buffer;
	size_t size;
	size_t data_size;
	int pos;
	unsigned char lang[4];
};

static int pipe_fd;
static struct connection *conns;

static struct pack *rpc_pak;

// unpack utilities
// rpc uses network byte order (big endian)
//! Get command field from buf
static inline unsigned int
get_cmd(const unsigned char *buf)
{
	return buf[0];
}

//! Returns data size of buf
static inline unsigned int
get_data_size(const unsigned char *buf)
{
	return buf[3] + (buf[2] << 8) + (buf[1] << 16);
}

//! Gets id field from buf
static inline unsigned int
get_id(const unsigned char *buf)
{
	return buf[3] + (buf[2] << 8) + (buf[1] << 16) + (buf[0] << 24);
}

//! Get size of buf
static inline unsigned int
get_size(const unsigned char *buf)
{
	return buf[1] + (buf[0] << 8);
}

//! Create a pipe
static int
create_pipe(const char *pipe_name)
{
    /*!
    Creates a pipe, with listen. length of the queue is 5
    @return Returns -2 if can't assign address to socket \n
    Returns -3 if can't listen requests
    */

	struct sockaddr_un name;
	size_t size;

	pipe_fd = socket(PF_LOCAL, SOCK_STREAM, 0);
	if (pipe_fd < 0) return -1;

    // delete cfg_socket_name
	unlink(pipe_name);

	name.sun_family = AF_LOCAL;
	strncpy(name.sun_path, pipe_name, sizeof(name.sun_path));
	size = (offsetof(struct sockaddr_un, sun_path) + strlen(name.sun_path) + 1);
    // assign address to socket
	if (0 != bind(pipe_fd, (struct sockaddr *) &name, size)) {
		close(pipe_fd);
		return -2;
	}

	chmod(pipe_name, 0666);

    // to enable connection requests on the socket ( a server socket )
	if (0 != listen(pipe_fd, 5)) {
		close(pipe_fd);
		return -3;
	}

	return 0;
}

//! get peer
static int
get_peer(int sock, struct Creds *cred)
{
    /*!
    Gets options of sock, and fills cred according to these options
    @return Returns 0. Returns -1 on error.
    */
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

//! Adds a new connection to connections chain
static void
add_conn(int sock)
{
	static int unsigned cookie = 0;
	struct connection *c;

	c = calloc(1, sizeof(struct connection));
	if (!c) {
		close(sock);
		return;
	}

	if (0 != get_peer(sock, &c->cred) || !acl_can_connect(&c->cred)) {
		close(sock);
		free(c);
		return;
	}

	c->sock = sock;
	c->notify_mask = notify_alloc();
	if (!c->notify_mask) {
		close(sock);
		free(c);
		return;
	}
	c->size = 256;
	c->buffer = malloc(256);
	if (!c->buffer) {
		close(sock);
		free(c->notify_mask);
		free(c);
		return;
	}
	c->cookie = cookie++;

	c->next = conns;
	c->prev = NULL;
	if (conns) conns->prev = c;
	conns = c;
}

//! Removes a connection from connections chain
static void
rem_conn(struct connection *c)
{
	close(c->sock);
	if (c->prev) c->prev->next = c->next;
	if (c->next) c->next->prev = c->prev;
	if (conns == c) conns = c->next;
	if (c->notify_mask) free(c->notify_mask);
	if (c->buffer) free(c->buffer);
	if (comar_shutting_down) {
		// FIXME: send a cancel all my jobs command here
	}
	free(c);
}

struct arg_s {
	unsigned char *buffer;
	size_t size;
	int pos;
};

//! Gets size and arguments from args. Checks for utf8 validation
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
	// arguments must be valid utf8
	if (!utf8_is_valid(*argp, *sizep)) return -1;
	args->pos += size;
	if (args->buffer[args->pos] != '\0') return -1;
	++args->pos;
	return 1;
}

//! write_rpc
static int
write_rpc(struct connection *c, unsigned int cmd, int id, const char *buffer, size_t size)
{
    /*!
    Checks the command cmd, and sends c's socket the answer
    */

	unsigned char head[8];

	head[4] = (id >> 24) & 0xFF;
	head[5] = (id >> 16) & 0xFF;
	head[6] = (id >> 8) & 0xFF;
	head[7] = id & 0xFF;

	if (RPC_RESULT == cmd || RPC_FAIL == cmd || RPC_NONE == cmd || RPC_ERROR == cmd) {
		char *s;
		size_t sz;

		pack_get(rpc_pak, &s, &sz);
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

//! rpc parse
static int
parse_rpc(struct connection *c)
{
    /*!
    This is parser function for RPC
    According to command in c's buffer, checks for permissions
    and executes, denies etc. the command
    */

	struct ipc_struct ipc;
	struct arg_s args;
	int cmd, no;
	char *t;
	size_t sz;

	memset(&ipc, 0, sizeof(struct ipc_struct));
	ipc.source.chan = (void *) c;
	ipc.source.cookie = c->cookie;
	ipc.source.id = get_id(c->buffer + 4);
	ipc.source.lang[0] = c->lang[0];
	ipc.source.lang[1] = c->lang[1];
	cmd = get_cmd(c->buffer);

//printf("RPC cmd %d, id %d, size %d\n", cmd, id, c->data_size);

	args.buffer = c->buffer + 8;
	args.pos = 0;
	args.size = c->data_size;

	switch (cmd) {
		case RPC_SHUTDOWN:
			// no parameter
			if (!acl_is_capable(CMD_SHUTDOWN, 0, &c->cred)) return -1;
			proc_put(TO_PARENT, CMD_SHUTDOWN, NULL, NULL);
			write_rpc(c, RPC_RESULT, ipc.source.id, NULL, 0);
			return 0;

		case RPC_REGISTER:
			// class name, package name, file name
			if (get_arg(&args, &t, &sz) != 1) return -1;
			no = model_lookup_class(t);
			if (no == -1) return -1;
			if (!acl_is_capable(CMD_REGISTER, no, &c->cred)) return -1;
			ipc.node = no;
			pack_reset(rpc_pak);
			if (get_arg(&args, &t, &sz) != 1) return -1;
			pack_put(rpc_pak, t, sz);
			if (get_arg(&args, &t, &sz) != 1) return -1;
			pack_put(rpc_pak, t, sz);
			if (get_arg(&args, &t, &sz) != 0) return -1;
			proc_put(TO_PARENT, CMD_REGISTER, &ipc, rpc_pak);
			return 0;

		case RPC_REMOVE:
			// package name
			if (!acl_is_capable(CMD_REMOVE, 0, &c->cred)) return -1;
			if (get_arg(&args, &t, &sz) != 1) return -1;
			pack_reset(rpc_pak);
			pack_put(rpc_pak, t, sz);
			if (get_arg(&args, &t, &sz) != 0) return -1;
			proc_put(TO_PARENT, CMD_REMOVE, &ipc, rpc_pak);
			return 0;

		case RPC_CHECKACL:
			// method name
			if (get_arg(&args, &t, &sz) != 1) return -1;
			no = model_lookup_method(t);
			if (no == -1) return -1;
			ipc.node = no;
			if (!acl_is_capable(CMD_CALL, no, &c->cred)) {
				write_rpc(c, RPC_DENIED, ipc.source.id, NULL, 0);
			} else {
				write_rpc(c, RPC_RESULT, ipc.source.id, NULL, 0);
			}
			return 0;

		case RPC_CALL:
			// method name, arg pairs (key-value)
			if (get_arg(&args, &t, &sz) != 1) return -1;
			no = model_lookup_method(t);
			if (no == -1) return -1;
			if (!acl_is_capable(CMD_CALL, no, &c->cred)) {
				write_rpc(c, RPC_DENIED, ipc.source.id, NULL, 0);
				return 0;
			}
			ipc.node = no;
			pack_reset(rpc_pak);
			while (1) {
				int ret = get_arg(&args, &t, &sz);
				if (ret == 0) break;
				if (ret == -1) return -1;
				if (!model_has_argument(no,  t)) return -1;
				pack_put(rpc_pak, t, sz);
				if (get_arg(&args, &t, &sz) != 1) return -1;
				pack_put(rpc_pak, t, sz);
			}
			proc_put(TO_PARENT, CMD_CALL, &ipc, rpc_pak);
			return 0;

		case RPC_CALL_PACKAGE:
			// method name, package name, arg pairs (key-value)
			if (get_arg(&args, &t, &sz) != 1) return -1;
			no = model_lookup_method(t);
			if (no == -1) return -1;
			if (!acl_is_capable(CMD_CALL, no, &c->cred)) {
				write_rpc(c, RPC_DENIED, ipc.source.id, NULL, 0);
				return 0;
			}
			ipc.node = no;
			if (get_arg(&args, &t, &sz) != 1) return -1;
			pack_reset(rpc_pak);
			pack_put(rpc_pak, t, sz);
			while (1) {
				int ret = get_arg(&args, &t, &sz);
				if (ret == 0) break;
				if (ret == -1) return -1;
				if (!model_has_argument(no,  t)) return -1;
				pack_put(rpc_pak, t, sz);
				if (get_arg(&args, &t, &sz) != 1) return -1;
				pack_put(rpc_pak, t, sz);
			}
			proc_put(TO_PARENT, CMD_CALL_PACKAGE, &ipc, rpc_pak);
			return 0;

		case RPC_EVENT:
			// class name, function name, app name, data
			if (get_arg(&args, &t, &sz) != 1) return -1;
			no = model_lookup_class(t);
			if (!acl_is_capable(CMD_EVENT, no, &c->cred)) return -1;
			ipc.node = no;
			pack_reset(rpc_pak);
			if (get_arg(&args, &t, &sz) != 1) return -1;
			pack_put(rpc_pak, t, sz);
			if (get_arg(&args, &t, &sz) != 1) return -1;
			pack_put(rpc_pak, t, sz);
			if (get_arg(&args, &t, &sz) != 1) return -1;
			pack_put(rpc_pak, t, sz);
			proc_put(TO_PARENT, CMD_EVENT, &ipc, rpc_pak);
			return 0;

		case RPC_CANCEL:
			// no parameter
			proc_put(TO_PARENT, CMD_CANCEL, &ipc, NULL);
			return 0;

		case RPC_GETLIST:
			// class name
			if (get_arg(&args, &t, &sz) != 1) return -1;
			no = model_lookup_class(t);
			if (no == -1) return -1;
			if (!acl_is_capable(CMD_CALL, no, &c->cred)) {
				write_rpc(c, RPC_DENIED, ipc.source.id, NULL, 0);
				return 0;
			}
			ipc.node = no;
			proc_put(TO_PARENT, CMD_GETLIST, &ipc, NULL);
			return 0;

		case RPC_ASKNOTIFY:
			// notify name
			if (get_arg(&args, &t, &sz) != 1) return -1;
			if (notify_mark(c->notify_mask, t) != 0) return -1;
			return 0;

		case RPC_DUMP_PROFILE:
			// no parameter
			if (!acl_is_capable(CMD_DUMP_PROFILE, 0, &c->cred)) return -1;
			proc_put(TO_PARENT, CMD_DUMP_PROFILE, &ipc, NULL);
			return 0;

		case RPC_LOCALIZE:
			if (get_arg(&args, &t, &sz) != 1) return -1;
			if (sz != 2) return -1;
			c->lang[0] = t[0];
			c->lang[1] = t[1];
			return 0;

		default:
			return -1;
	}
}

//! Read from rpc from c's socket to c's buffer
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
		if (c->data_size + 8 >= c->size) {
			while (c->data_size + 8 >= c->size) {
				c->size *= 2;
			}
			c->buffer = realloc(c->buffer, c->size);
			if (!c->buffer) return -1;
		}
	}
	if (c->pos == c->data_size + 8) {
		if (parse_rpc(c)) return -1;
		c->data_size = 0;
		c->pos = 0;
	}
	return 0;
}

//! set sockets for all connections
static int
add_rpc_fds(fd_set *fds, int max)
{
	struct connection *c;

	// listening pipe
	if (!comar_shutting_down) {
		FD_SET(pipe_fd, fds);
		if (pipe_fd >= max) max = pipe_fd + 1;
	}
	// current connections
	for (c = conns; c; c = c->next) {
		FD_SET(c->sock, fds);
		if (c->sock >= max) max = c->sock + 1;
	}
	return max;
}

//! This is handler function for custom rpc commands
void
handle_rpc_fds(fd_set *fds)
{
	struct connection *c;
	int sock;

	if (!comar_shutting_down && FD_ISSET(pipe_fd, fds)) {
		// new connection
		struct sockaddr_un cname;
		size_t size = sizeof(cname);
		sock = accept(pipe_fd, (struct sockaddr *)&cname, &size);
		if (sock != -1) add_conn(sock);
	}

	c = conns;
	while (c) {
		if (FD_ISSET(c->sock, fds)) {
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

//! This function gets the reply and sends it to connection with cmd command
void
forward_reply(struct ProcChild *p, size_t size, int cmd)
{
	struct ipc_struct ipc;
	struct connection *c;
	char *s;
	size_t sz;

	proc_get(p, &ipc, rpc_pak, size);
	for (c = conns; c; c = c->next) {
		if (c == (struct connection *) ipc.source.chan && c->cookie == ipc.source.cookie) {
			pack_get(rpc_pak, &s, &sz);
			write_rpc(c, cmd, ipc.source.id, s, sz);
			return;
		}
	}
}

//! Main RPC process
static void
rpc_proc(void)
{
	struct ipc_struct ipc;
	struct ProcChild *p;
	struct connection *c;
	fd_set fds;
	int max;
	int cmd;
	size_t size;
	char *s;
	size_t sz;

	rpc_pak = pack_new(1024);

	if (create_pipe(cfg_socket_name) != 0) {
		log_error("RPC_UNIX: Cannot create listening pipe '%s'\n", cfg_socket_name);
		return;
	}
	log_info("RPC_UNIX: listening on %s\n", cfg_socket_name);

	while (1) {
		max = proc_setup_fds(&fds);
		max = add_rpc_fds(&fds, max);
		if (1 == proc_select_fds(&fds, max, &p, &cmd, &size, -1)) {
			switch (cmd) {
				case CMD_SHUTDOWN:
					comar_shutting_down = 1;
					close(pipe_fd);
					pipe_fd = -1;
					break;
				case CMD_NOTIFY:
					proc_get(p, &ipc, rpc_pak, size);
					pack_get(rpc_pak, &s, &sz);
					for (c = conns; c; c = c->next) {
						if (notify_is_marked(c->notify_mask, ipc.node)) {
							write_rpc(c, RPC_NOTIFY, 0, s, sz);
						}
					}
					break;
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
				case CMD_CUSTOM:
					handle_rpc_fds(&fds);
					break;
				default:
					// this shouldn't happen, warn and skip
					log_error("RPC: Unexpected internal command %d\n", cmd);
					proc_get(p, &ipc, rpc_pak, size);
			}
		}
	}
}

//! rpc start
void
rpc_unix_start(void)
{
    /*!
    Fork RPC process
    @return Returns -1 on error
    */

	struct ProcChild *p;

	p = proc_fork(rpc_proc, "ComarRPC");
	if (!p) exit(1);
}
