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

#include "model.h"

enum {
	N_MODULE,
	N_OBJECT,
	N_METHOD
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

int
model_init(void)
{
	int no;

	// FIXME: silly test case, replace with real loader
	if (prepare_tables(4, 128)) return -1;

	no = add_node(-1, "Net", N_MODULE);
	no = add_node(no, "Net.NIC", N_OBJECT);
	add_node(no, "Net.NIC.up", N_METHOD);
	add_node(no, "Net.NIC.down", N_METHOD);

	return 0;
}

int
model_lookup_object(const char *path)
{
	struct node *n;
	int val;

	val = hash_string(path, strlen(path)) % TABLE_SIZE;
	for (n = node_table[val]; n; n = n->next) {
		if (N_OBJECT == n->type && strcmp(n->path, path) == 0) {
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
