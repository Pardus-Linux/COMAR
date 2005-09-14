/*
** Copyright (c) 2005, TUBITAK/UEKAE
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
	int parent_no;
	int type;
	int no;
};

#define TABLE_SIZE 367

int model_max_notifications;
static int nr_nodes;
static struct node **node_table;
static struct node *nodes;
static char *paths;

static unsigned int
hash_string(const unsigned char *str, int len)
{
	unsigned int h = 0, i;

	for (i = 0; i < len; i++) {
		h = ( h << 5 ) - h + str[i];
	}
	return h;
}

static int
prepare_tables(int max_nodes, size_t str_size)
{
	nodes = calloc(max_nodes, sizeof(struct node));
	node_table = calloc(TABLE_SIZE, sizeof(struct node *));
	paths = malloc(str_size);
	if (!nodes || !node_table || !paths) return -1;
	return 0;
}

static int
add_node(int parent_no, const char *path, int type)
{
	struct node *n;
	int val;
	int len = strlen(path);

	n = &nodes[nr_nodes];
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
	n->no = nr_nodes++;

	val = hash_string(path, len) % TABLE_SIZE;
	n->next = node_table[val];
	node_table[val] = n;

	return n->no;
}

static char *
build_path(iks *g, iks *o, iks *m)
{
	static char *ptr = NULL;

	if (ptr) {
		ptr += strlen(ptr) + 1;
	} else {
		ptr = paths;
	}

	if (m) {
		sprintf(ptr, "%s.%s.%s",
			iks_find_attrib(g, "name"),
			iks_find_attrib(o, "name"),
			iks_find_attrib(m, "name")
		);
	} else if (o) {
		sprintf(ptr, "%s.%s",
			iks_find_attrib(g, "name"),
			iks_find_attrib(o, "name")
		);
	} else {
		strcpy(ptr, iks_find_attrib(g, "name"));
	}

	return ptr;
}

int
model_init(void)
{
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
					}
				}
			}
		}
	}

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
						if (iks_strcmp(iks_name(met), "method") == 0) {
							add_node(obj_no, build_path(grp, obj, met), N_METHOD);
						} else if (iks_strcmp(iks_name(met), "notify") == 0) {
							add_node(obj_no, build_path(grp, obj, met), N_NOTIFY);
							++model_max_notifications;
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

int
model_lookup_method(const char *path)
{
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

int
model_lookup_notify(const char *path)
{
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

int
model_parent(int node_no)
{
	struct node *n;

	n = &nodes[node_no];
	return n->parent_no;
}

const char *
model_get_method(int node_no)
{
	struct node *n;

	n = &nodes[node_no];
	return n->method;
}

const char *
model_get_path(int node_no)
{
	struct node *n;

	n = &nodes[node_no];
	return n->path;
}
