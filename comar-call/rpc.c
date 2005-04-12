/*
** Copyright (c) 2004, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** comar-call - rpc.c
** comard unix rpc client
*/

#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <stdarg.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <obstack.h>

#include "rpc.h"

static const char sock_name[] = "/tmp/comar-test";
static int sock = -1;

int
rpc_connect(void)
{
	struct sockaddr_un name;
	size_t size;

	sock = socket(PF_LOCAL, SOCK_STREAM, 0);
	if (sock == -1) {
		fprintf(stderr, "Cannot create unix socket\n");
		return -1;
	}
	name.sun_family = AF_LOCAL;
	strncpy(name.sun_path, sock_name, sizeof (name.sun_path));
	size = (offsetof (struct sockaddr_un, sun_path) + strlen (name.sun_path) + 1);
	if (connect(sock, (struct sockaddr *) &name, size) != 0) {
		fprintf(stderr, "connect('%s') failed\n", sock_name);
		return -2;
	}
	return 0;
}

#define obstack_chunk_alloc malloc
#define obstack_chunk_free free

static void
my_strcat(struct obstack *ob, const char *fmt, ...)
{
	static char buf[256];
	va_list ap;

	va_start(ap, fmt);
	vsnprintf(buf, sizeof (buf), fmt, ap);
	va_end(ap);
	obstack_grow(ob, buf, strlen (buf));
}

int
rpc_send(int type, char *tts_id, char *rpc_data)
{
	struct obstack ob;
	char *str;

	obstack_init(&ob);

	my_strcat(&ob, "<COMARRPCData>");
	my_strcat(&ob, "<RPCVersion>1.0</RPCVersion>");
	my_strcat(&ob, "<RPCTTSID>%s</RPCTTSID>", tts_id);
	my_strcat(&ob, "<RPCEOLTime>0</RPCEOLTime>");
	switch (type & 0xF0) {
		case RPC_DONTCARE:
			my_strcat(&ob, "<RPCPriority>DONTCARE</RPCPriority>");
			break;
		case RPC_INTERACTIVE:
			my_strcat(&ob, "<RPCPriority>INTERACTIVE</RPCPriority>");
			break;
	}
	switch (type & 0xF) {
		case RPC_OMCALL:
			my_strcat(&ob, "<RPCType>OMCALL</RPCType>");
			break;
	}
	my_strcat(&ob, "<RPCData>");
	obstack_grow(&ob, rpc_data, strlen(rpc_data));
	my_strcat(&ob, "</RPCData>");
	my_strcat(&ob, "</COMARRPCData>");

	obstack_1grow(&ob, 0);
	str = obstack_finish(&ob);
printf("SEND[%s]\n\n",str);
	send(sock, str, strlen (str), 0);
	obstack_free(&ob, NULL);

	return 0;
}

static const char paramstr[] = "%s<parameter><name>%s</name><value><string encoding='tr'>%s</string></value></parameter>";

// FIXME: string escape problemi
char *
rpc_add_string(char *parameters, char *name, char *value)
{
	char *ret, *old;
	int len = 0;

	if (parameters) len = strlen(parameters);
	len += strlen(name);
	len += strlen(value);
	len += strlen(paramstr);

	ret = malloc(len);
	if (parameters) old = parameters; else old = "";
	sprintf(ret, paramstr, old, name, value);
	if (parameters) free(parameters);
	return ret;
}

static const char callstr[] = "<type>method</type><name>%s</name><index>0</index><parameters>%s</parameters>";

char *
rpc_make_call(int type, char *node, char *parameters)
{
	char *ret, *pars;

	if (parameters) pars = parameters; else pars = "";
	ret = malloc(strlen(callstr) + strlen(node) + strlen(pars));
	sprintf(ret, callstr, node, pars);
	if (parameters) free(parameters);
	return ret;
}

void
rpc_recv(void)
{
	char buf[1024];
	int len;
	while (1) {
		len = recv(sock, buf, 1023, 0);
		if (len == 0) break;
		if (len == -1) {
			puts("baglanti erken kesildi");
			break;
		}
printf("RECV[%s]\n\n", buf);
	}
}

void
rpc_disconnect(void)
{
	close(sock);
	sock = -1;
}
