/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#ifndef RPC_H
#define RPC_H 1

// rpc/ipc commands
enum {
	CMD_DIED,
	CMD_FAIL,
	CMD_RESULT,
	CMD_REGISTER,
	CMD_REMOVE,
	CMD_CALL
};

struct ipc_data {
	int node;
	size_t app_len;
	char data[4];
};

void rpc_unix_start(void);


#endif /* RPC_H */
