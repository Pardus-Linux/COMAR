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
#include <stdarg.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <unistd.h>

#include "comar.h"

// unpack utilities
// rpc uses network byte order (big endian)
static unsigned int
get_cmd(const unsigned char *buf)
{
	return buf[0];
}

static unsigned int
get_data_size(const unsigned char *buf)
{
	return buf[3] + (buf[2] << 8) + (buf[1] << 16);
}

static unsigned int
get_id(const unsigned char *buf)
{
	return buf[3] + (buf[2] << 8) + (buf[1] << 16) + (buf[0] << 24);
}

static const char *cmdnames[] = {
	COMAR_CMD_NAMES
};


struct comar_struct {
	int sock;
	unsigned int id;
	int cmd;
	unsigned char *buffer;
	size_t max;
	size_t size;
	char *pakname;
};

comar_t *
comar_connect(void)
{
	comar_t *com;
	struct sockaddr_un name;
	size_t size;

	com = calloc(1, sizeof(struct comar_struct));
	if (!com) return NULL;

	com->sock = socket(PF_LOCAL, SOCK_STREAM, 0);
	if (com->sock == -1) {
		free(com);
		return NULL;
	}

	name.sun_family = AF_LOCAL;
	strncpy(name.sun_path, COMAR_PIPE_NAME, sizeof (name.sun_path));
	size = (offsetof (struct sockaddr_un, sun_path) + strlen (name.sun_path) + 1);
	if (connect(com->sock, (struct sockaddr *) &name, size) != 0) {
		close(com->sock);
		free(com);
		return NULL;
	}
	return com;
}

int
comar_get_fd(comar_t *com)
{
	return com->sock;
}

const char *
comar_cmd_name(int cmd)
{
	if (cmd >= 0 || cmd < COMAR_CMD_MAX)
		return cmdnames[cmd];
	else
		return "Unknown";
}

void
comar_send_start(comar_t *com, unsigned int id, int cmd)
{
	com->id = id;
	com->cmd = cmd;
	com->size = 0;
}

int
comar_send_arg(comar_t *com, const char *str, size_t size)
{
	size_t need;
	unsigned char *p;

	if (0 == size) size = strlen(str);

	need = com->size + 2 + size + 1;
	if (com->max < need) {
		if (0 == com->max) {
			com->max = 128;
		} else {
			while (com->max < need) com->max *= 2;
		}
		com->buffer = realloc(com->buffer, com->max);
		if (!com->buffer) return 0;
	}
	p = com->buffer + 8 + com->size;
	p[0] = size >> 8;
	p[1] = size & 0xFF;
	p += 2;
	strcpy(p, str);
	com->size = need;
	return 1;
}

int
comar_send_finish(comar_t *com)
{
	unsigned char *buf;

	buf = com->buffer;
	// cmd + size
	buf[0] = com->cmd;
	buf[1] = (com->size >> 16) & 0xFF;
	buf[2] = (com->size >> 8) & 0xFF;
	buf[3] = com->size & 0xFF;
	// id
	buf[4] = com->id >> 24;
	buf[5] = (com->id >> 16) & 0xFF;
	buf[6] = (com->id >> 8) & 0xFF;
	buf[7] = com->id & 0xFF;

	send(com->sock, buf, 8 + com->size, 0);

	return 1;
}

int
comar_send(comar_t *com, unsigned int id, int cmd, ...)
{
	va_list ap;
	char *str;

	comar_send_start(com, id, cmd);

	va_start(ap, cmd);
	while (1) {
		str = va_arg(ap, char*);
		if (!str) break;
		comar_send_arg(com, str, 0);
	}
	va_end(ap);

	return comar_send_finish(com);
}

int
comar_wait(comar_t *com, int timeout)
{
	fd_set fds;
	struct timeval tv;
	struct timeval *tvp;

	FD_ZERO(&fds);
	FD_SET(com->sock, &fds);
	tv.tv_sec = timeout;
	tv.tv_usec = 0;
	if (timeout != -1) tvp = &tv; else tvp = NULL;

	if (select(com->sock + 1, &fds, NULL, NULL, tvp) > 0) {
		return 1;
	}
	return 0;
}

int
comar_read(comar_t *com, int *cmdp, unsigned int *idp, char **strp)
{
	size_t size;
	size_t len;
	unsigned char head[8];
	char *buf;

	len = recv(com->sock, head, 8, 0);
	if (len < 8) return 0;
	*cmdp = get_cmd(head);
	*idp = get_id(head + 4);
	*strp = NULL;
	size = get_data_size(head);
	if (size) {
		if (size >= com->max) {
			if (0 == com->max) {
				com->max = size + 1;
			} else {
				while (com->max < size) com->max *= 2;
			}
			com->buffer = realloc(com->buffer, com->max);
		}
		len = 0;
		buf = com->buffer;
		while (len < size) {
			len += recv(com->sock, buf + len, size - len, 0);
		}
		buf[size] = '\0';
		if (*cmdp == COMAR_RESULT) {
			char *t;
			t = strchr(buf, ' ');
			if (t) {
				*t = '\0';
				com->pakname = buf;
				*strp = t + 1;
			}
			return 1;
		}
		*strp = buf;
	}
	return 1;
}

char *
comar_package_name(comar_t *com)
{
	return com->pakname;
}

void
comar_disconnect(comar_t *com)
{
	close(com->sock);
	if (com->buffer) free(com->buffer);
	free(com);
}
