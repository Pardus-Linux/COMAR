/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#ifndef COMAR_H
#define COMAR_H 1

#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>

#define COMAR_PIPE_NAME "/var/run/comar.socket"

// comar rpc commands, keep in sync with rpc_unix.c
// commands from the daemon
#define COMAR_RESULT 0
#define COMAR_FAIL 1
#define COMAR_NONE 2
#define COMAR_DENIED 3
#define COMAR_ERROR 4
#define COMAR_RESULT_START 5
#define COMAR_RESULT_END 6
#define COMAR_NOTIFY 7
// commands to the daemon
#define COMAR_LOCALIZE 8
#define COMAR_REGISTER 9
#define COMAR_REMOVE 10
#define COMAR_CALL 11
#define COMAR_CALL_PACKAGE 12
#define COMAR_ASKNOTIFY 13
#define COMAR_GETLIST 14
#define COMAR_CHECKACL 15
#define COMAR_DUMP_PROFILE 16
#define COMAR_CANCEL 17
#define COMAR_EVENT 18

#define COMAR_CMD_MAX 19
#define COMAR_CMD_NAMES \
	"Result", \
	"Fail", \
	"None", \
	"Denied", \
	"Error", \
	"ResultStart", \
	"ResultEnd", \
	"Notify", \
	"Localize", \
	"Register", \
	"Remove", \
	"Call", \
	"CallPackage", \
	"AskNotify", \
	"GetList", \
	"CheckACL", \
	"DumpProfile", \
	"Cancel", \
	"Event",

struct comar_struct;
typedef struct comar_struct comar_t;

comar_t *comar_connect(void);
int comar_get_fd(comar_t *com);
const char *comar_cmd_name(int cmd);
void comar_send_start(comar_t *com, unsigned int id, int cmd);
int comar_send_arg(comar_t *com, const char *str, size_t size);
int comar_send_finish(comar_t *com);
int comar_send(comar_t *com, unsigned int id, int cmd, ...);
int comar_wait(comar_t *com, int timeout);
int comar_read(comar_t *com, int *cmdp, unsigned int *idp, char **strp);
char *comar_package_name(comar_t *com);
void comar_disconnect(comar_t *com);


#ifdef __cplusplus
}
#endif

#endif	/* COMAR_H */
