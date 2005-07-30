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

// ipc commands
enum {
	CMD_DIED,
	CMD_FAIL,
	CMD_RESULT,
	CMD_REGISTER,
	CMD_REMOVE,
	CMD_CALL
};

void ipc_start(int cmd, void *caller_data, int node);
void ipc_pack_arg(const char *arg);
void ipc_pack_pair(const char *key, const char *value);
void ipc_send(struct ProcChild *p);

int ipc_recv(struct ProcChild *p, size_t size);
int ipc_get_node(void);
void *ipc_get_data(void);
char *ipc_get_arg(void);
int ipc_get_pair(char **keyp, char **valuep);


#endif /* IPC_H */
