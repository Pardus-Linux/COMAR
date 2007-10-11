/*
** Copyright (c) 2005-2006, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "i18n.h"
#include "iksemel.h"
#include "cfg.h"
#include "log.h"
#include "model.h"

//! enum for model
enum {
	N_GROUP,
	N_CLASS,
	N_METHOD,
	N_NOTIFY
};

struct node {
	const char *path;
	const char *method;
	struct node *next;
	const char *args;
	int nr_instances;
	int nr_args;
	int flags;
	int parent_no;
	int type;
	int no;
	void *acldata;
	int level;
};

#define TABLE_SIZE 367

int model_max_notifications;
int model_nr_nodes;
static struct node **node_table;
static struct node *nodes;
static char *paths;

//! hash string elements and return hash number
static unsigned int
hash_string(const unsigned char *str, int len)
{
	unsigned int h = 0, i;

	for (i = 0; i < len; i++) {
		h = ( h << 5 ) - h + str[i];
	}
	return h;
}

//! Create table
static int
prepare_tables(int max_nodes, size_t str_size)
{
    /*!
    @return Returns 0 if successfully allocates memory for nodes, node table and paths,
    -1 otherwise
    */

	nodes = calloc(max_nodes, sizeof(struct node));
	node_table = calloc(TABLE_SIZE, sizeof(struct node *));
	paths = malloc(str_size);
	if (!nodes || !node_table || !paths) return -1;
	return 0;
}

//! Add a node to table
static int
add_node(int parent_no, const char *path, int type)
{
    /*!
    parent_no is depth of node. adds node with path and type (method)
    to node table
    */

	struct node *n;
	int val;
	int len = strlen(path);

	n = &nodes[model_nr_nodes];
	n->path = path;
	if (type == N_METHOD) {
		n->method = path + len;
		while (n->method[-1] != '.')
			--n->method;
	} else {
		n->method = NULL;
	}
	n->parent_no = parent_no;
	n->type = type;
	n->no = model_nr_nodes++;

	val = hash_string(path, len) % TABLE_SIZE;
	n->next = node_table[val];
	node_table[val] = n;

	return n->no;
}

static char *path_ptr = NULL;

//!
static char *
build_path(iks *g, iks *o, iks *m)
{
    /*!
    Returns the 'name' attr of 'g' iks node (group)
    if 'm' is given, returns it as group.object.method (names)
    if 'o' is given, returns group.object (names)
    */

	if (path_ptr) {
		path_ptr += strlen(path_ptr) + 1;
	} else {
		path_ptr = paths;
	}

	if (m) {
		sprintf(path_ptr, "%s.%s.%s",
			iks_find_attrib(g, "name"),
			iks_find_attrib(o, "name"),
			iks_find_attrib(m, "name")
		);
	} else if (o) {
		sprintf(path_ptr, "%s.%s",
			iks_find_attrib(g, "name"),
			iks_find_attrib(o, "name")
		);
	} else {
		strcpy(path_ptr, iks_find_attrib(g, "name"));
	}

	return path_ptr;
}

static char *
build_arg(int no, int is_instance, const char *name)
{
	if (path_ptr) {
		path_ptr += strlen(path_ptr) + 1;
	} else {
		path_ptr = paths;
	}

	if (is_instance)
		nodes[no].nr_instances++;
	else
		nodes[no].nr_args++;
	
	strcpy(path_ptr, name);
	if (NULL == nodes[no].args)
		nodes[no].args = path_ptr;

	return path_ptr;
}

//! Model initialize
int
model_init(void)
{
    /*!
    This function parses model.xml file (cfg_model_file)
    Converts model.xml's access levels and flags to ACL levels and
    flags, and loads into memory before deleting dom tree
    \sa cfg.c
    */

	iks *model;
	iks *grp, *obj, *met;
	int count = 0;
	size_t size = 0;
	size_t grp_size, obj_size, met_size;
	int grp_no, obj_no;
	int e;

	// parse model file
	e = iks_load(cfg_model_file, &model);
	if (e) {
		log_error("Cannot process model file '%s'\n", cfg_model_file);
		return -1;
	}

	if (iks_strcmp(iks_name(model), "comarModel") != 0) {
		log_error("Not a COMAR model file '%s'\n", cfg_model_file);
		return -1;
	}

	// FIXME: ugly code ahead, split into functions and simplify

	// scan the model
	for (grp = iks_first_tag(model); grp; grp = iks_next_tag(grp)) {
		if (iks_strcmp(iks_name(grp), "group") == 0) {
			grp_size = iks_strlen(iks_find_attrib(grp, "name"));
			if (!grp_size) {
				log_error("Broken COMAR model file '%s'\n", cfg_model_file);
				return -1;
			}
			size += grp_size + 1;
			++count;
			for (obj = iks_first_tag(grp); obj; obj = iks_next_tag(obj)) {
				if (iks_strcmp(iks_name(obj), "class") == 0) {
					obj_size = iks_strlen(iks_find_attrib(obj, "name"));
					if (!obj_size) {
						log_error("Broken COMAR model file '%s'\n", cfg_model_file);
						return -1;
					}
					size += grp_size + obj_size + 2;
					++count;
					for (met = iks_first_tag(obj); met; met = iks_next_tag(met)) {
						if (iks_strcmp(iks_name(met), "method") == 0
							|| iks_strcmp(iks_name(met), "notify") == 0) {
							met_size = iks_strlen(iks_find_attrib(met, "name"));
							if (!met_size) {
								log_error("Broken COMAR model file '%s'\n", cfg_model_file);
								return -1;
							}
							size += grp_size + obj_size + met_size + 3;
							++count;
						}
						if (iks_strcmp(iks_name(met), "method") == 0) {
							iks *arg;
							for (arg = iks_first_tag(met); arg; arg = iks_next_tag(arg)) {
								if (iks_strcmp(iks_name(arg), "argument") == 0
									|| iks_strcmp(iks_name(arg), "instance") == 0) {
									size += iks_cdata_size(iks_child(arg)) + 1;
								}
							}
						}
					}
				}
			}
		}
	}

    // size is counted to alloc mem for paths
	// prepare data structures
	if (prepare_tables(count, size)) return -1;

	// load the model
	for (grp = iks_first_tag(model); grp; grp = iks_next_tag(grp)) {
		if (iks_strcmp(iks_name(grp), "group") == 0) {
			grp_no = add_node(-1, build_path(grp, NULL, NULL), N_GROUP);
			for (obj = iks_first_tag(grp); obj; obj = iks_next_tag(obj)) {
				if (iks_strcmp(iks_name(obj), "class") == 0) {
					obj_no = add_node(grp_no, build_path(grp, obj, NULL), N_CLASS);
					for (met = iks_first_tag(obj); met; met = iks_next_tag(met)) {
						int no;
						if (iks_strcmp(iks_name(met), "method") == 0) {
							iks *arg;
							char *prof;
							no = add_node(obj_no, build_path(grp, obj, met), N_METHOD);
							prof = iks_find_attrib(met, "access");
							if (prof) {
								if (strcmp(prof, "user") == 0)
									nodes[no].level = ACL_USER;
								if (strcmp(prof, "guest") == 0)
									nodes[no].level = ACL_GUEST;
							}
							prof = iks_find_attrib(met, "profile");
							if (prof) {
								if (strcmp(prof, "global") == 0)
									nodes[no].flags |= P_GLOBAL;
								if (strcmp(prof, "package") == 0)
									nodes[no].flags |= P_PACKAGE;
							}
							prof = iks_find_attrib(met, "profileOp");
							if (prof) {
								if (strcmp(prof, "delete") == 0)
									nodes[no].flags |= P_DELETE;
								if (strcmp(prof, "startup") == 0)
									nodes[no].flags |= P_STARTUP;
							}
							for (arg = iks_first_tag(met); arg; arg = iks_next_tag(arg)) {
								if (iks_strcmp(iks_name(arg), "instance") == 0) {
									build_arg(no, 1, iks_cdata(iks_child(arg)));
								}
							}
							for (arg = iks_first_tag(met); arg; arg = iks_next_tag(arg)) {
								if (iks_strcmp(iks_name(arg), "argument") == 0) {
									char *argname;
									argname = iks_cdata(iks_child(arg));
									if (argname) {
										build_arg(no, 0, argname);
									} else {
										log_error("Argument name needed in <argument> tag of model.xml\n");
									}
								}
							}
						} else if (iks_strcmp(iks_name(met), "notify") == 0) {
							no = add_node(obj_no, build_path(grp, obj, met), N_NOTIFY);
							if (no >= model_max_notifications)
								model_max_notifications = no + 1;
						}
					}
				}
			}
		}
	}

	// no need to keep dom tree in memory
	iks_delete(model);

	return 0;
}

//! Look for a class in node table @return Returns the matcing node number or -1 otherwise
int
model_lookup_class(const char *path)
{
	struct node *n;
	int val;

	val = hash_string(path, strlen(path)) % TABLE_SIZE;
	for (n = node_table[val]; n; n = n->next) {
		if (N_CLASS == n->type && strcmp(n->path, path) == 0) {
			return n->no;
		}
	}
	return -1;
}

//! Look for a method in node table
int
model_lookup_method(const char *path)
{
    /*!
    Lookup a method in node table.
    @return If found, returns its number in table, returns -1 otherwise·
    */

	struct node *n;
	int val;

	val = hash_string(path, strlen(path)) % TABLE_SIZE;
	for (n = node_table[val]; n; n = n->next) {
		if (N_METHOD == n->type && strcmp(n->path, path) == 0) {
			return n->no;
		}
	}
	return -1;
}

//! Look for a notify in node table
int
model_lookup_notify(const char *path)
{
    /*!
    If specified path's record in node table has a type of 'notify'
    returns its number in table, returns -1 otherwise
    */

	struct node *n;
	int val;

	val = hash_string(path, strlen(path)) % TABLE_SIZE;
	for (n = node_table[val]; n; n = n->next) {
		if (N_NOTIFY == n->type && strcmp(n->path, path) == 0) {
			return n->no;
		}
	}
	return -1;
}

//! Get parent of node_no
int
model_parent(int node_no)
{
    /*!
    if node_no numbered record in node table is a method, returns its parent number
    else returns node_no
    */

	struct node *n;

	n = &nodes[node_no];
	if (n->type == N_METHOD)
		return n->parent_no;
	return node_no;
}

//! Return the method of node numbered 'node_no'
const char *
model_get_method(int node_no)
{
	struct node *n;

	n = &nodes[node_no];
	return n->method;
}

//! Return path of a node from node table
const char *
model_get_path(int node_no)
{
	struct node *n;

	n = &nodes[node_no];
	return n->path;
}

//! Find argument
int
model_has_argument(int node_no, const char *argname)
{
    /*!
    @return Returns 1 if argname is found in node table, 0 otherwise
    */

	struct node *n;
	int max, i;
	const char *t;

	if (!argname || argname[0] == '\0') return 0;

	n = &nodes[node_no];
	max = n->nr_instances + n->nr_args;
	if (!max) return 0;
	t = n->args;
	for (i = 0; i < max; i++) {
		if (strcmp(t, argname) == 0) return 1;
		t += strlen(t) + 1;
	}
	return 0;
}

//! return flags of 'node_no' from node table
int
model_flags(int node_no)
{
	return nodes[node_no].flags;
}

//! Looks for number of instances of node_no.
//! @return Returns 1 if has an instance, 0 otherwise
int
model_has_instances(int node_no)
{
	if (nodes[node_no].nr_instances) return 1;
	return 0;
}

//! If argname is an instance of node_no, returns 1, 0 otherwise
int
model_is_instance(int node_no, const char *argname)
{
	struct node *n;
	int max, i;
	const char *t;

	n = &nodes[node_no];
	max = n->nr_instances;
	if (!max) return 0;
	t = n->args;
	for (i = 0; i < max; i++) {
		if (strcmp(t, argname) == 0) return 1;
		t += strlen(t) + 1;
	}
	return 0;
}

//! Return args of node_no from node table
const char *
model_instance_key(int node_no)
{
	return nodes[node_no].args;
}

//! Given acldata with node_no is set in node table \sa acl.c
void
model_acl_set(int node_no, void *acldata)
{
	struct node *n;

	n = &nodes[node_no];
	n->acldata = acldata;
}

//! Get acl from node table
void
model_acl_get(int node_no, void **acldatap, unsigned int *levelp)
{
    /*!
    This function gets 'acldata' and 'level' from node table, from record numbered 'node_no'
    \param acldatap is pointer to acldata
    \param levelp is pointer to level
    */

	struct node *n;

	n = &nodes[node_no];
	if (n->type != N_CLASS) {
		*levelp = n->level;
		n = &nodes[n->parent_no];
	} else {
		*levelp = ACL_GUEST;
	}
	*acldatap = n->acldata;
}

//! Find next class
int
model_next_class(int *class_nop)
{
    /*!
    Scans node table for class tags
    @return If found, returns 1 and sets the node number to given argument (class_nop) \n
    Returns 0 if no classes found
    */

	int no;
	struct node *n;

	no = *class_nop;
	do {
		++no;
		n = &nodes[no];
		if (N_CLASS == n->type) {
			*class_nop = no;
			return 1;
		}
	} while (no < model_nr_nodes);
	*class_nop = -1;
	return 0;
}
