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

#define COMAR_PIPE_NAME "/tmp/comar"

// comar rpc commands, keep in sync with rpc_unix.c
// commands from the daemon
#define COMAR_RESULT 0
#define COMAR_FAIL 1
#define COMAR_DENIED 2
#define COMAR_RESULT_START 3
#define COMAR_RESULT_END 4
#define COMAR_NOTIFY 5
// commands to the daemon
#define COMAR_LOCALIZE 6
#define COMAR_REGISTER 7
#define COMAR_REMOVE 8
#define COMAR_CALL 9
#define COMAR_CALL_PACKAGE 10
#define COMAR_ASKNOTIFY 11
#define COMAR_GETLIST 12
#define COMAR_CHECKACL 13

struct comar_struct;
typedef struct comar_struct comar_t;

comar_t *comar_connect(void);
int comar_send(comar_t *com, unsigned int id, int cmd, ...);
void comar_disconnect(comar_t *com);


#endif	/* COMAR_H */
