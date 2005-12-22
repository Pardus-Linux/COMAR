/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#ifndef IPC_H
#define IPC_H 1

#include "utility.h"

// ipc commands
enum {
	CMD_FINISH = 0,
	CMD_RESULT,
	CMD_RESULT_START,
	CMD_RESULT_END,
	CMD_FAIL,
	CMD_NONE,
	CMD_ERROR,
	CMD_REGISTER,
	CMD_REMOVE,
	CMD_CALL,
	CMD_CALL_PACKAGE,
	CMD_GETLIST,
	CMD_NOTIFY,
	CMD_DUMP_PROFILE,
	CMD_SHUTDOWN,
	CMD_EVENT
};

void ipc_start(int cmd, void *caller_data, int id, int node);
void ipc_pack_arg(const char *arg, size_t size);
void ipc_send(struct ProcChild *p);

int ipc_recv(struct ProcChild *p, size_t size);
int ipc_get_node(void);
void *ipc_get_data(void);
int ipc_get_id(void);
int ipc_get_arg(char **argp, size_t *sizep);

struct pack *ipc_into_pack(void);


#endif /* IPC_H */
