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


#endif /* IPC_H */
