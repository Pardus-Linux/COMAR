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
#include <stddef.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <unistd.h>

#include "libcomar.h"

struct comar_struct {
	int sock;
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
comar_send(comar_t *com, unsigned int id, int cmd, ...)
{
	va_list ap;
	size_t size = 0;
	size_t len;
	char *str;
	char *buf;
	char *p;

	buf = malloc(8);

	// arguments
	va_start(ap, cmd);
	p = buf + 8;
	while (1) {
		str = va_arg(ap, char*);
		if (!str) break;
		len = strlen(str);
		buf = realloc(buf, 8 + size + 2 + len + 1);
		p = buf + 8 + size;
		p[0] = len >> 8;
		p[1] = len & 0xFF;
		p += 2;
		strcpy(p, str);
		size += 2 + len + 1;
	}
	va_end(ap);

	// cmd + size
	buf[0] = cmd;
	buf[1] = (size >> 16) & 0xFF;
	buf[2] = (size >> 8) & 0xFF;
	buf[3] = size & 0xFF;
	// id
	buf[4] = id >> 24;
	buf[5] = (id >> 16) & 0xFF;
	buf[6] = (id >> 8) & 0xFF;
	buf[7] = id & 0xFF;

	send(com->sock, buf, 8 + size, 0);

	return 0;
}

void
comar_disconnect(comar_t *com)
{
	close(com->sock);
	free(com);
}

#ifdef COMAR_TEST
int
main(int argc, char *argv[])
{
	comar_t *com;

	com = comar_connect();
	comar_send(com, 0, COMAR_CALL, "Time.Clock.getDate", NULL);

	return 0;
}
#endif
