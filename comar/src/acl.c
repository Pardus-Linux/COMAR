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

#define TABLE_SIZE 47

struct acl_node {
	struct acl_node *next;
	unsigned int id;
	unsigned int nr_nodes;
	unsigned int node[1];
};

struct acl_list {
	struct acl_node *admins[TABLE_SIZE];
	struct acl_node *users[TABLE_SIZE];
	struct acl_node *guests[TABLE_SIZE];
};

static struct acl_list acl_uids;
static struct acl_list acl_gids;

static struct acl_node *
get_node(struct acl_node **table, unsigned int id)
{
	struct acl_node *n;
	unsigned int val;

	val = id % TABLE_SIZE;
	for (n = table[val]; n; n = n->next) {
		if (n->id == id) {
			return n;
		}
	}
	return NULL;
}

static void
delete_node(struct acl_node **table, unsigned int id)
{
	struct acl_node *n;
	struct acl_node *old = NULL;
	unsigned int val;

	val = id % TABLE_SIZE;
	for (n = table[val]; n; n = n->next) {
		if (n->id == id) {
			if (old) {
				old->next = n->next;
			} else {
				table[val] = n->next;
			}
			free(n);
			return;
		}
		old = n;
	}
}

static void
set_node(struct acl_node **table, unsigned int id, char *nodes)
{
	struct acl_node *n;
	char *t, *s;
	unsigned int val;
	int nr_nodes = 0;
	int i = 0;

	t = nodes;
	while (t) {
		++nr_nodes;
		t = strchr(t, ' ');
		if (t) ++t;
	}

	n = calloc(1, sizeof(struct acl_node) + nr_nodes * sizeof(int));
	if (!n) return;
	n->id = id;
	n->nr_nodes = nr_nodes;
	for (t = nodes; t; t = s) {
		s = strchr(t, ' ');
		if (s) {
			*s = '\0';
			++s;
		}
		n->node[i++] = model_lookup_class(t);
	}

	val = id % TABLE_SIZE;
	n->next = table[val];
	table[val] = n;
}

static void
set_nodes(struct acl_list *tables, unsigned int id, char *nodes)
{
	char *t;

	t = strchr(nodes, '\n');
	*t = '\0';
	++t;

	delete_node(tables->admins, id);
	if (nodes[0] != '\0')
		set_node(tables->admins, id, nodes);

	nodes = t;
	t = strchr(nodes, '\n');
	*t = '\0';
	++t;

	delete_node(tables->users, id);
	if (nodes[0] != '\0')
		set_node(tables->users, id, nodes);

	nodes = t;

	delete_node(tables->guests, id);
	if (nodes[0] != '\0')
		set_node(tables->guests, id, nodes);
}

static int
check_acl(int node, struct Creds *cred)
{
	gid_t gids[64];
	int nr_gids = 64;
	struct passwd *pw;
	struct acl_node *n;
	int i;

	node = model_parent(node);

	n = get_node(acl_uids.admins, cred->uid);
	if (n) {
		for (i = 0; i < n->nr_nodes; i++) {
			if (n->node[i] == node)
				return 1;
		}
	}

	pw = getpwuid(cred->uid);
	if (!pw) return 0;
	if (getgrouplist(pw->pw_name, cred->gid, &gids[0], &nr_gids) < 0) {
		nr_gids = 63;
	}

	for (i = 0; i < nr_gids; i++) {
		n = get_node(acl_gids.admins, gids[i]);
		if (n) {
			for (i = 0; i < n->nr_nodes; i++) {
				if (n->node[i] == node)
					return 1;
			}
		}
	}

	return 0;
}

int
acl_is_capable(int cmd, int node, struct Creds *cred)
{
	// root always capable
	if (cred->uid == 0)
		return 1;

	if (cmd == CMD_CALL) {
		if (check_acl(node, cred) == 1)
			return 1;
	}

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

void
acl_init(void)
{
	// FIXME: read from db
	set_nodes(&acl_gids, 10, strdup("System.Package System.Service Time.Clock Net.Stack Net.Link Net.Filter\n\n"));
}
