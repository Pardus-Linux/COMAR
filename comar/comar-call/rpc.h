/*
** Copyright (c) 2004, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** comar-call - rpc.h
** comard unix rpc client header
*/

#define RPC_OMCALL 0x1

#define RPC_DONTCARE 0x00
#define RPC_INTERACTIVE 0x10

#define RPC_METHOD 0
#define RPC_PROPGET 1
#define RPC_PROPSET 2

int rpc_connect(void);
char *rpc_add_string(char *parameters, char *name, char *value);
char *rpc_make_call(int type, char *node, char *parameters);
int rpc_send(int type, char *tts_id, char *rpc_data);
void rpc_recv(void);
void rpc_disconnect(void);
