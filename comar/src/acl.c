/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <stdlib.h>

#include "acl.h"
#include "process.h"
#include "ipc.h"

int
acl_is_capable(int cmd, int node, struct Creds *cred)
{
	// test policy: allow calls for everyone
	switch (cmd) {
		case CMD_REGISTER:
		case CMD_REMOVE:
		case CMD_SHUTDOWN:
		case CMD_DUMP_PROFILE:
			// only root allowed
			if (cred->uid == 0) return 1;
			break;
		case CMD_CALL:
			// FIXME: must check acl db
			// test policy: allow calls for everyone
			return 1;
	}
	return 0;
}
