/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <stdlib.h>
#include <string.h>
#include <pwd.h>
#include <grp.h>

#include "acl.h"
#include "process.h"
#include "ipc.h"
#include "log.h"

int
acl_is_capable(int cmd, int node, struct Creds *cred)
{
	/* POLICY:
	** Pardus 1.0 release
	** Only root can use admin commands
	** Users can make configuration calls
	*/

	// root always capable
	if (cred->uid == 0)
		return 1;

	if (cmd == CMD_CALL)
		return 1;

	return 0;
}

int
acl_can_connect(struct Creds *cred)
{
	/* POLICY:
	** Pardus 1.0 release
	** Only wheel group users can connect and use comar
	*/
	struct group *grp;
	struct passwd *pwd;
	int i;

	// root always allowed
	if (cred->uid == 0)
		return 1;

	grp = getgrnam("wheel");
	if (!grp) {
		log_error("No 'wheel' group in password database!\n");
		return 0;
	}

	pwd = getpwuid(cred->uid);
	if (!pwd) {
		log_error("User id %d has no entry in password database!\n", cred->uid);
		return 0;
	}

	for (i = 0; grp->gr_mem[i]; i++) {
		if (strcmp(pwd->pw_name, grp->gr_mem[i]) == 0)
			return 1;
	}

	return 0;
}
