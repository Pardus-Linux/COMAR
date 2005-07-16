/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <db.h>

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/stat.h>

#include "cfg.h"
#include "data.h"

static DB_ENV *my_env;
static int nr_open_dbs;

int
db_init(void)
{
	struct stat fs;

	if (stat(cfg_data_dir, &fs) != 0) {
		if (0 != mkdir(cfg_data_dir, S_IRWXU)) {
			printf("Cannot create data dir '%s'\n", cfg_data_dir);
			return -1;
		}
	} else {
		// FIXME: check perms and owner
	}
	// FIXME: check and recover db files
	return 0;
}

static DB *
open_db(const char *name)
{
	DB *db;
	int e;

	// join the environment if necessary
	if (!my_env) {
		e  = db_env_create(&my_env, 0);
		if (e) {
			printf("Cannot create env, %s\n", db_strerror(e));
			return NULL;
		}
		e = my_env->open(my_env, cfg_data_dir, DB_INIT_LOCK | DB_INIT_MPOOL
				| DB_INIT_LOG | DB_INIT_TXN | DB_CREATE, 0);
		if (e) {
			printf("Cannot open env, %s\n", db_strerror(e));
			my_env->close(my_env, 0);
			my_env = NULL;
			return NULL;
		}
	}

	// open db
	e = db_create(&db, my_env, 0);
	if (e) {
		printf("Cannot create db, %s\n", db_strerror(e));
		if (0 == nr_open_dbs) {
			my_env->close(my_env, 0);
			my_env = NULL;
		}
		return NULL;
	}
	e = db->open(db, NULL, name, NULL, DB_BTREE, DB_CREATE, 0);
	if (e) {
		printf("Cannot open db, %s\n", db_strerror(e));
		db->close(db, 0);
		if (0 == nr_open_dbs) {
			my_env->close(my_env, 0);
			my_env = NULL;
		}
		return NULL;
	}

	nr_open_dbs++;
	return db;
}

static void
close_db(DB *db)
{
	db->close(db, 0);
	--nr_open_dbs;
	if (0 == nr_open_dbs) {
		my_env->close(my_env, 0);
		my_env = NULL;
	}
}

static char *
get_data(DB *db, const char *name, int rw_lock, int *errorp)
{
	DBT pair[2];

	memset(&pair[0], 0, sizeof(DBT) * 2);
	pair[0].data = (char *) name;
	pair[0].size = strlen(name);
	pair[1].flags = DB_DBT_MALLOC;

	*errorp = db->get(db, NULL, &pair[0], &pair[1], 0);
	if (*errorp == 0) return pair[1].data;
	return NULL;
}

static int
put_data(DB *db, const char *name, const char *data, size_t size)
{
	DBT pair[2];

	memset(&pair[0], 0, sizeof(DBT) * 2);
	pair[0].data = (char *) name;
	pair[0].size = strlen(name);
	pair[1].data = (char *) data;
	pair[1].size = size;
	return db->put(db, NULL, &pair[0], &pair[1], 0);
}

static int
del_data(DB *db, const char *name)
{
	DBT key;

	memset(&key, 0, sizeof(DBT));
	key.data = (char *) name;
	key.size = strlen(name);
	return db->del(db, NULL, &key, 0);
}

static const char *
make_key(int node_no, const char *app)
{
	// FIXME: lame
	static char buf[128];

	if (node_no != -1 && app)
		sprintf(buf, "%d/%s", node_no, app);
	else if (app == NULL)
		sprintf(buf, "%d", node_no);
	else
		return app;
	return buf;
}

static char *
make_list(char *old, const char *item)
{
	// FIXME: lame
	char *ret;

	if (strcmp(old, "") != 0) {
		ret = malloc(strlen(old) + 1 + strlen(item) + 1);
		sprintf(ret, "%s/%s", old, item);
	} else {
		ret = malloc(strlen(item) + 1);
		sprintf(ret, "%s", item);
	}
	return ret;
}

int
db_put_script(int node_no, const char *app, const char *buffer, size_t size)
{
	DB *code_db = NULL, *model_db = NULL, *app_db = NULL;
	char *old;
	int e, ret = -1;

	app_db = open_db("app.db");
	if (!app_db) goto out;
	model_db = open_db("model.db");
	if (!model_db) goto out;
	code_db = open_db("code.db");
	if (!code_db) goto out;

	old = get_data(app_db, app, 0, &e);
	if (!old) {
		if (e == DB_NOTFOUND)
			old = "";
		else
			goto out;
	}

	if (strstr(old, make_key(node_no, NULL)) == NULL) {
		char *t = make_list(old, make_key(node_no, NULL));
		e = put_data(app_db, app, t, strlen(t) + 1);
		free(t);
		if (e) goto out;
	}
	if (strcmp(old, "") != 0) free(old);

	e = put_data(code_db, make_key(node_no, app), buffer, size);
	if (e) goto out;

	old = get_data(model_db, make_key(node_no, NULL), 0, &e);
	if (!old) {
		if (e == DB_NOTFOUND)
			old = "";
		else
			goto out;
	}

	if (strstr(old, app) == NULL) {
		char *t = make_list(old, app);
		e = put_data(model_db, make_key(node_no, NULL), t, strlen(t + 1));
		free(t);
		if (e) goto out;
	}
	if (strcmp(old, "") != 0) free(old);

	ret = 0;
out:
	if (code_db) close_db(code_db);
	if (model_db) close_db(model_db);
	if (app_db) close_db(app_db);
	return ret;
}

int
db_del_app(const char *app)
{
	DB *code_db = NULL, *model_db = NULL, *app_db = NULL;
	char *list, *list2, *t, *s;
	int e, ret = -1;

	app_db = open_db("app.db");
	if (!app_db) goto out;
	model_db = open_db("model.db");
	if (!model_db) goto out;
	code_db = open_db("code.db");
	if (!code_db) goto out;

	list = get_data(app_db, app, 0, &e);
	if (!list) goto out;

	printf("app %s registered (%s)\n", app, list);

	for (t = list; t; t = s) {
		s = strchr(t, '/');
		if (s) {
			*s = '\0';
			++s;
		}

		list2 = get_data(model_db, t, 0, &e);
		if (!list2) goto out;
printf("del model(%s) %s\n", t, list2);
		{
			char *k;
			int sa = strlen(app);
			k = strstr(list2, app);
			if (k) {
				if (k[sa] == '/') ++sa;
				memmove(k, k + sa, strlen(k) - sa + 1);
printf("new node list '%s'\n", list2);
				e = put_data(model_db, t, list2, strlen(list2) + 1);
				if (e) goto out;
			}
		}
		free(list2);

		e = del_data(code_db, make_key(atoi(t), app));
		if (e) goto out;
	}

	free(list);

printf("del app (%s)\n", app);
	e = del_data(app_db, app);
	if (e) goto out;

	ret = 0;
out:
	if (code_db) close_db(code_db);
	if (model_db) close_db(model_db);
	if (app_db) close_db(app_db);
	return ret;
}

static DB *n_code_db;
static int n_node_no;

int
db_open_node(int node_no, char **bufferp)
{
	DB *model_db = NULL;
	int e, ret = -1;

	model_db = open_db("model.db");
	if (!model_db) return -1;

	*bufferp = get_data(model_db, make_key(node_no, NULL), 0, &e);
	if (e) goto out;

	n_code_db = open_db("code.db");
	if (!n_code_db) goto out;
	n_node_no = node_no;

	ret = 0;
out:
	if (model_db) close_db(model_db);
	return ret;
}

int
db_get_code(const char *app, char **bufferp, size_t *sizep)
{
	DBT key, data;
	int e;

	memset(&key, 0, sizeof(DBT));
	memset(&data, 0, sizeof(DBT));
	key.data = (char *) make_key(n_node_no, app);
	key.size = strlen(key.data);
	data.flags = DB_DBT_MALLOC;

	e = n_code_db->get(n_code_db, NULL, &key, &data, 0);
	if (e) return -1;

	*bufferp = data.data;
	*sizep = data.size;
	return 0;
}

void
db_close_node(void)
{
	close_db(n_code_db);
}
