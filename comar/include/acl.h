/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#ifndef ACL_H
#define ACL_H 1

struct Creds {
	uid_t uid;
	gid_t gid;
	// there'll be other fields
};

int acl_is_capable(int cmd, int node, struct Creds *cred);


#endif /* ACL_H */
