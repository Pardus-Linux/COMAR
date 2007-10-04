/*
** Copyright (c) 2005-2006, TUBITAK/UEKAE
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
#include "model.h"
#include "log.h"
#include "iksemel.h"

//! access control group, a group id and level
struct acl_group {
	gid_t gid;
	unsigned int level;
};

struct acl_class {
	unsigned int nr_groups;
	unsigned int cur;
	struct acl_group group[1];
};

static gid_t *acl_allowed_gids;
static unsigned int acl_nr_allowed_gids;

//! Count groups
static int
count_groups(iks *tag, int class_no)
{
	/*!
	Returns the number of group tags in child tags of 'tag'
	It also counts group tags under class tag ( class permissions )
	@return Returns number of groups
	*/
	iks *x;
	unsigned int nr = 0;
	// global permissions
	for (x = iks_find(tag, "group"); x; x = iks_next_tag(x)) {
		if (iks_strcmp(iks_name(x), "group") == 0)
			++nr;
	}
	// class permissions
	x = iks_find_with_attrib(tag, "class", "name", model_get_path(class_no));
	for (x = iks_find(x, "group"); x; x = iks_next_tag(x)) {
		if (iks_strcmp(iks_name(x), "group") == 0)
			++nr;
	}
	return nr;
}

//! add_allowed
static void
add_allowed(gid_t gid)
{
	/*!
	This function allocates memory for allowed group id's. @see acl_allowed_gids
	Every group is added once
	*/
	static unsigned int max_allowed = 0;
	unsigned int i;

	if (acl_allowed_gids) {
		if (acl_nr_allowed_gids >= max_allowed) {
			gid_t *tmp = realloc(acl_allowed_gids, max_allowed * 2 * sizeof(gid_t));
			if (!tmp) return;
			max_allowed *= 2;
			acl_allowed_gids = tmp;
		}
	} else {
		max_allowed = 8;
		acl_allowed_gids = calloc(max_allowed, sizeof(gid_t));
		if (!acl_allowed_gids) return;
	}
	for (i = 0; i < acl_nr_allowed_gids; i++) {
		if (acl_allowed_gids[i] == gid)
			return;
	}
	acl_allowed_gids[acl_nr_allowed_gids++] = gid;
}

//! add_group
static void
add_group(iks *tag, int level, struct acl_class *ac)
{
	/*!
	Scans the 'tag's 'name' attribute, and searches the result in groups database (unix groups db)
	When found, numerical group id and level is set to current group structure
	\param ac is the allocated memory for acl_group structure \param level is permissions level
	*/
	struct acl_group *ag;
	char *name;
	struct group *grp;

	ag = &ac->group[ac->cur];
	name = iks_find_attrib(tag, "name");
	if (!name) return;
	grp = getgrnam(name);
	if (!grp) {
		log_error("Security policy group '%s' not available\n", name);
		return;
	}
	add_allowed(grp->gr_gid);
	ag->gid = grp->gr_gid;
	ag->level = level;
	++ac->cur;
}

//! add_groups
static void
add_groups(iks *tag, int class_no, int level, struct acl_class *ac)
{
	/*!
	Searches 'tag' in 'group' and 'class' tags, calls add_group function with found tags
	level and acl_class is passed to add_group
	\sa add_group
	*/
	iks *x;
	// global permissions
	for (x = iks_find(tag, "group"); x; x = iks_next_tag(x)) {
		if (iks_strcmp(iks_name(x), "group") == 0)
			add_group(x, level, ac);
	}
	// class permissions
	x = iks_find_with_attrib(tag, "class", "name", model_get_path(class_no));
	for (x = iks_find(x, "group"); x; x = iks_next_tag(x)) {
		if (iks_strcmp(iks_name(x), "group") == 0)
			add_group(x, level, ac);
	}
}

//! set_class
static void
set_class(iks *model, int class_no)
{
	/*!
	Allocates memory for all found 'group's in 'model' @see count_groups()
	Then add_groups is called and acl_class is put in node table
	\sa add_groups
	*/
	struct acl_class *ac;
	int nr_groups = 0;

	nr_groups += count_groups(iks_find(model, "admin"), class_no);
	nr_groups += count_groups(iks_find(model, "user"), class_no);
	nr_groups += count_groups(iks_find(model, "guest"), class_no);

	ac = calloc(1, sizeof(struct acl_class) + (nr_groups * sizeof(struct acl_group)));
	if (!ac) return;
	ac->nr_groups = nr_groups;

	add_groups(iks_find(model, "admin"), class_no, ACL_ADMIN, ac);
	add_groups(iks_find(model, "user"), class_no, ACL_USER, ac);
	add_groups(iks_find(model, "guest"), class_no, ACL_GUEST, ac);

	model_acl_set(class_no, ac);
}

//! access control initialize
void
acl_init(void)
{
	/*!
	Loads /etc/comar/security-policy.xml file
	For all classes in model.xml file look in security-policy if theres a match
	*/
	iks *policy;
	iks *model;
	int class_no;
	int e;

	// parse security policy file
	e = iks_load("/etc/comar/security-policy.xml", &policy);
	if (e) {
		log_error("Cannot process security policy file '%s', error %d\n",
			"/etc/comar/security-policy.xml", e);
		return;
	}
	if (iks_strcmp(iks_name(policy), "comarSecurityPolicy") != 0) {
		log_error("Not a security policy file '%s'\n",
			"/etc/comar/security-policy.xml");
		return;
	}

	// call permissions on the model
	model = iks_find(policy, "model");
	if (model) {
		class_no = -1;
		while (model_next_class(&class_no)) {
			set_class(model, class_no);
		}
	}
}

//! check_acl
static int
check_acl(int node, struct Creds *cred)
{
	/*!
	Checks if cred->uid user is capable to perform the action,
	@return Returns 1 if capable, 0 otherwise
	*/
	gid_t gids[64];
	int nr_gids = 64;
	struct passwd *pw;
	struct acl_class *ac;
	struct acl_group *ag;
	void *acptr = &ac;
	int level;
	int i, j;

	model_acl_get(node, acptr, &level);
	if (!ac) return 0;

	pw = getpwuid(cred->uid);
	if (!pw) return 0;
	if (getgrouplist(pw->pw_name, cred->gid, &gids[0], &nr_gids) < 0) {
		nr_gids = 63;
	}

	for (i = 0; i < nr_gids; i++) {
		for (j = 0; j < ac->nr_groups; j++) {
			ag = &ac->group[j];
			if (gids[i] == ag->gid) {
				if (ag->level <= level)
					return 1;
				else
					break;
			}
		}
	}

	return 0;
}

//! Find if user is ok to exec cmd
int
acl_is_capable(int cmd, int node, struct Creds *cred)
{
	/*!
	Checks if cred->uid user is capable executing command cmd.
	Root is always capable, only CMD_CALL commands are allowed here
	@return Returns 1 if allowed, 0 otherwise
	*/
	// root always capable
	if (cred->uid == 0)
		return 1;

	if (cmd == CMD_CALL) {
		if (check_acl(node, cred) == 1)
			return 1;
	}

	return 0;
}

//! Check if user can connect
int
acl_can_connect(struct Creds *cred)
{
	/*!
	Checks if user with user id cred->uid can connect comar.
	@return Returns 1 if can connect, 0 otherwise
	*/
	gid_t gids[64];
	int nr_gids = 64;
	struct passwd *pw;
	int i, j;

	// root always allowed
	if (cred->uid == 0)
		return 1;

	pw = getpwuid(cred->uid);
	if (!pw) return 0;
	if (getgrouplist(pw->pw_name, cred->gid, &gids[0], &nr_gids) < 0) {
		nr_gids = 63;
	}

	for (i = 0; i < nr_gids; i++) {
		for (j = 0; j < acl_nr_allowed_gids; j++) {
			if (gids[i] == acl_allowed_gids[j])
				return 1;
		}
	}

	return 0;
}
