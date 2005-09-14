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

int
acl_is_capable(int cmd, int node, struct Creds *cred)
{
	/* normal policy
	switch (cmd) {
		case CMD_REGISTER:
		case CMD_REMOVE:
			// only root allowed for administration
			if (cred->uid == 0)return 1;
			break;
		case CMD_CALL:
			// must check acl db
			return 1;
	}
	return 0;
	*/

	// test policy: allow everyone
	return 1;
}
