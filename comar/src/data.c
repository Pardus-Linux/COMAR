/*
** Copyright (c) 2005-2007, TUBITAK/UEKAE
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
#include <sys/file.h>
#include <unistd.h>

#include "cfg.h"
#include "data.h"
#include "model.h"
#include "log.h"
#include "process.h"
#include "utility.h"
#include "iksemel.h"

static int
check_db_format(void)
{
	FILE *f;
	size_t len;
	char *fmt_name;
	char *fmt;

	len = strlen(cfg_data_dir) + 7 + 1;
	fmt_name = malloc(len);
	if (!fmt_name) return 1;
	snprintf(fmt_name, len, "%s%s", cfg_data_dir, "/format");

	fmt = load_file(fmt_name, NULL);
	if (fmt) {
		if (atoi(fmt) != 1 && atoi(fmt) != 2) {
			log_error("Unsupported database format '%s'\n", fmt);
			return 1;
		}
		free(fmt);
	} else {
		f = fopen(fmt_name, "w");
		if (!f) {
			log_error("Cannot write to '%s'\n", fmt_name);
			return 1;
		}
		fwrite("1", 1, 1, f);
		fclose(f);
	}

	free(fmt_name);
	return 0;
}

static char *code_lock_name;

int
db_init(void)
{
	struct stat fs;
	size_t size;

	if (stat(cfg_data_dir, &fs) != 0) {
		if (0 != mkdir(cfg_data_dir, S_IRWXU)) {
			log_error("Cannot create data dir '%s'\n", cfg_data_dir);
			return -1;
		}
	} else {
		// FIXME: check perms and owner
	}

	if (check_db_format()) return -2;

	size = strlen(cfg_data_dir) + 11;
	code_lock_name = malloc(size);
	if (!code_lock_name) return -3;
	snprintf(code_lock_name, size, "%s/code", cfg_data_dir);
	if (stat(code_lock_name, &fs) != 0) {
		if (0 != mkdir(code_lock_name, S_IRWXU)) {
			log_error("Cannot create data dir '%s'\n", code_lock_name);
			return -1;
		}
	}
	snprintf(code_lock_name, size, "%s/code/lock", cfg_data_dir);

	// FIXME: check and recover db files
	return 0;
}

struct databases {
	DB_ENV *env;
	DB *model;
	DB *app;
	DB *code;
	DB *profile;
};

#define MODEL_DB 1
#define APP_DB 2
#define CODE_DB 4
#define PROFILE_DB 8

static int
open_database(DB_ENV *env, DB **dbp, const char *name)
{
	int e;
	DB *db;

	e = db_create(dbp, env, 0);
	if (e) {
		log_error("Cannot create database, %s\n", db_strerror(e));
		*dbp = NULL;
		return -1;
	}
	db = *dbp;
	e = db->open(db, NULL, name, NULL, DB_BTREE, DB_CREATE, 0);
	if (e) {
		log_error("Cannot open database, %s\n", db_strerror(e));
		return -2;
	}
	return 0;
}

static int
open_env(struct databases *db, int which)
{
	int e;

	memset(db, 0, sizeof(struct databases));
	e = db_env_create(&db->env, 0);
	if (e) {
		log_error("Cannot create database environment, %s\n", db_strerror(e));
		db->env = NULL;
		return -1;
	}
	e = db->env->open(db->env,
		cfg_data_dir,
		DB_INIT_LOCK |DB_INIT_MPOOL | DB_INIT_LOG | DB_INIT_TXN | DB_CREATE,
		0
	);
	if (e) {
		log_error("Cannot open database environment, %s\n", db_strerror(e));
		return -2;
	}

	if (which & MODEL_DB) {
		if (open_database(db->env, &db->model, "model.db")) return -3;
	}
	if (which & APP_DB) {
		if (open_database(db->env, &db->app, "app.db")) return -4;
	}
	if (which & CODE_DB) {
		if (open_database(db->env, &db->code, "code.db")) return -5;
	}
	if (which & PROFILE_DB) {
		if (open_database(db->env, &db->profile, "profile.db")) return -6;
	}

	return 0;
}

static void
close_env(struct databases *db)
{
	if (db->profile) db->profile->close(db->profile, 0);
	if (db->code) db->code->close(db->code, 0);
	if (db->app) db->app->close(db->app, 0);
	if (db->model) db->model->close(db->model, 0);
	db->env->close(db->env, 0);
}

static char *
get_data(DB *db, const char *name, size_t *sizep, int *errorp)
{
	DBT pair[2];

	memset(&pair[0], 0, sizeof(DBT) * 2);
	pair[0].data = (char *) name;
	pair[0].size = strlen(name);
	pair[1].flags = DB_DBT_MALLOC;

	*errorp = db->get(db, NULL, &pair[0], &pair[1], 0);
	if (*errorp == 0) {
		if (sizep) *sizep = pair[1].size;
		return pair[1].data;
	}
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

static char *
make_key(int node_no, const char *app)
{
	const char *path;
	char *key;
	size_t size;

	path = model_get_path(node_no);
	size = strlen(path) + 1 + strlen(app) + 1;

	key = malloc(size);
	if (!key) return NULL;
	snprintf(key, size, "%s/%s", path, app);

	return key;
}

static int
append_item(DB *db, const char *key, const char *item)
{
	char *t, *s;
	char *old;
	char *data;
	size_t len;
	int e;

	old = get_data(db, key, NULL, &e);
	if (e && e != DB_NOTFOUND) return -1;

	if (!old || old[0] == '\0') {
		// no old record
		e = put_data(db, key, item, strlen(item) + 1);
		if (e) return -1;
		return 0;
	}

	t = strdup(old);
	if (!t) return -1;
	for (; t; t = s) {
		s = strchr(t, '/');
		if (s) {
			*s = '\0';
			++s;
		}
		if (strcmp(t, item) == 0) {
			// already registered
			return 0;
		}
	}

	// append to old records
	len = strlen(old) + 1 + strlen(item) + 1;
	data = malloc(len);
	if (!data) return -1;
	snprintf(data, len, "%s/%s", old, item);

	e = put_data(db, key, data, strlen(data) + 1);
	if (e) return -1;

	return 0;
}

int
db_put_script(int node_no, const char *app, const char *buffer, size_t size)
{
	struct databases db;
	int e, ret = -1;

	if (open_env(&db, APP_DB | MODEL_DB)) goto out;

	e = append_item(db.app, app, model_get_path(node_no));
	if (e) goto out;

	e = append_item(db.model, model_get_path(node_no), app);
	if (e) goto out;

	ret = 0;
out:
	close_env(&db);
	if (ret == 0) {
		ret = db_save_code(node_no, app, buffer);
	}
	return ret;
}

int
db_del_app(const char *app)
{
	struct databases db;
	char *list, *list2, *t, *s;
	int e, ret = -1;
	int no;

	if (open_env(&db, APP_DB | MODEL_DB | CODE_DB)) goto out;

	list = get_data(db.app, app, NULL, &e);
	if (!list) goto out;

	for (t = list; t; t = s) {
		s = strchr(t, '/');
		if (s) {
			*s = '\0';
			++s;
		}

		list2 = get_data(db.model, t, NULL, &e);

		if (list2) {
			char *k;
			int sa = strlen(app);
			k = strstr(list2, app);
			if (k) {
				if (k[sa] == '/') ++sa;
				memmove(k, k + sa, strlen(k) - sa + 1);
				sa = strlen(list2);
				if (sa > 0) {
					if (list2[sa-1] == '/')
						list2[sa-1] = '\0';
				}
				e = put_data(db.model, t, list2, strlen(list2) + 1);
				if (e) goto out;
			}
		}
		free(list2);

		no = model_lookup_class(t);
		if (no != -1) {
			e = db_delete_code(no, app);
			e = del_data(db.code, make_key(no, app));
		}
	}

	free(list);

	e = del_data(db.app, app);
	if (e) goto out;

	ret = 0;
out:
	close_env(&db);
	return ret;
}

int
db_get_apps(int node_no, char **bufferp)
{
	struct databases db;
	int e, ret = -1;

	if (open_env(&db, MODEL_DB)) goto out;

	*bufferp = get_data(db.model, model_get_path(node_no), NULL, &e);
	if (e) goto out;

	ret = 0;
out:
	close_env(&db);
	return ret;
}

int
db_get_code(int node_no, const char *app, char **bufferp, size_t *sizep)
{
	struct databases db;
	char *key;
	int e, ret = -1;

	if (open_env(&db, CODE_DB)) goto out;

	key = make_key(node_no, app);
	if (!key) goto out;
	*bufferp = get_data(db.code, key, sizep, &e);
	if (e) goto out;

	ret = 0;
out:
	close_env(&db);
	return ret;
}

static char *
make_code_key(int node_no, const char *app)
{
	const char *path;
	char *key;
	char *t;
	size_t size;

	path = model_get_path(node_no);
	size = strlen(cfg_data_dir) + 6 + strlen(path) + 1 + strlen(app) + 4;

	key = malloc(size);
	if (!key) return NULL;

	snprintf(key, size, "%s/code/%s_%s.py", cfg_data_dir, path, app);

	for (t = key + size - 5; *t != '/'; t--) {
		if (*t == '.') *t = '_';
	}

	return key;
}

static int
lock_code_db(int is_exclusive)
{
	int fd;

	fd = open(code_lock_name, O_WRONLY | O_CREAT, 0600);
	if (fd == -1) {
		log_error("Code lock problem");
		// FIXME: handle better
		return -1;
	}
	if (is_exclusive)
		flock(fd, LOCK_EX);
	else
		flock(fd, LOCK_SH);
	return fd;
}

static void
unlock_code_db(int fd)
{
	flock(fd, LOCK_UN);
	close(fd);
}

int
db_load_code(int node_no, const char *app, char **bufferp)
{
	char *key;
	char *code;
	int fd;

	key = make_code_key(node_no, app);
	if (!key) return -1;

	fd = lock_code_db(0);
	code = load_file(key, NULL);
	unlock_code_db(fd);
	if (!code) return -2;

	*bufferp = code;
	return 0;
}

int
db_save_code(int node_no, const char *app, const char *buffer)
{
	char *key;
	int fd;
	int ret;

	key = make_code_key(node_no, app);
	if (!key) return -1;

	fd = lock_code_db(1);
	ret = save_file(key, buffer, strlen(buffer));
	unlock_code_db(fd);
	if (ret != 0) return -2;
	return 0;
}

int
db_delete_code(int node_no, const char *app)
{
	char *key;
	int fd;
	int ret;

	key = make_code_key(node_no, app);
	if (!key) return -1;

	fd = lock_code_db(1);
	ret = unlink(key);
	unlock_code_db(fd);
	if (ret != 0) return -2;
	return 0;
}

static char *
make_profile_key(int method, const char *app, const char *inst_key, const char *inst_value)
{
	size_t len;
	const char *node;
	char *inst_sep = "";
	char *key;

// key format: Node / [App] / [instance = [ value ] ]

	if (inst_key)
		// instances belong to the class
		node = model_get_path(model_parent(method));
	else
		// globals belong to the method
		node = model_get_path(method);

	len = strlen(node) + 3;

	if (app)
		len += strlen(app);
	else
		app = "";

	if (inst_key) {
		if (!inst_value) inst_value = "";
		len += strlen(inst_key) + 1 + strlen(inst_value);
		inst_sep = "=";
	} else {
		inst_key = "";
		inst_value = "";
	}

	key = malloc(len);
	if (!key) return NULL;

	snprintf(key, len, "%s/%s/%s%s%s", node, app, inst_key, inst_sep, inst_value);

	return key;
}

int
db_put_profile(int node_no, const char *app, struct pack *args)
{
	struct databases db;
	struct pack *old_args = NULL;
	int e, ret = -1;
	char *key = NULL;
	char *inst_key = NULL;
	char *inst_value = NULL;
	char *t, *t2, *data;
	size_t ts, size;

	if (open_env(&db, PROFILE_DB)) goto out;

	while (pack_get(args, &t, &ts)) {
		if (model_is_instance(node_no, t)) {
			inst_key = t;
			pack_get(args, &t, &ts);
			inst_value = t;
		} else {
			pack_get(args, &t, &ts);
		}
	}

	key = make_profile_key(node_no, app, inst_key, inst_value);
	if (!key) goto out;

	data = get_data(db.profile, key, &size, &e);
	// FIXME: handle notfound separately, see also csl.c/c_get_profile()
	if (e && e != DB_NOTFOUND) goto out;

	if (!e) {
		old_args = pack_wrap(data, size);
		args->pos = 0;
		while (pack_get(args, &t, &ts)) {
			pack_get(args,&t2, &ts);
			pack_replace(old_args, t, t2, ts);
		}
		e = put_data(db.profile, key, old_args->buffer, old_args->used);
	} else {
		e = put_data(db.profile, key, args->buffer, args->used);
	}

	if (e) goto out;

	ret = 0;
out:
	close_env(&db);
	if (old_args) pack_delete(old_args);
	if (key) free(key);
	return ret;
}

struct databases *blaa = NULL;

struct pack *
db_get_profile(int node_no, const char *app, const char *inst_key, const char *inst_value)
{
	struct databases db;
	struct pack *p = NULL;
	int e;
	char *key, *data;
	size_t size;

	if (!blaa) {
	if (open_env(&db, PROFILE_DB)) goto out;
	}

	// FIXME: multiple instance keys?
	key = make_profile_key(node_no, app, inst_key, inst_value);
	if (!key) goto out;
	if (blaa)
	data = get_data(blaa->profile, key, &size, &e);
	else
	data = get_data(db.profile, key, &size, &e);
	free(key);
	// FIXME: handle notfound separately, see also csl.c/c_get_profile()
	if (e) goto out;

	p = pack_wrap(data, size);

out:
	if (!blaa) close_env(&db);
	return p;
}

void
db_del_profile(int node_no, const char *app, struct pack *args)
{
	struct databases db;
	char *key = NULL;
	char *inst_key = NULL;
	char *inst_value = NULL;
	char *t;
	size_t ts;

	if (open_env(&db, PROFILE_DB)) goto out;

	while (pack_get(args, &t, &ts)) {
		if (model_is_instance(node_no, t)) {
			inst_key = t;
			pack_get(args, &t, &ts);
			inst_value = t;
		} else {
			pack_get(args, &t, &ts);
		}
	}

	key = make_profile_key(node_no, app, inst_key, inst_value);
	if (!key) goto out;

	del_data(db.profile, key);

out:
	if (key) free(key);
	close_env(&db);
}

int
db_get_instances(int node_no, const char *app, const char *key, void (*func)(char *str, size_t size))
{
	struct databases db;
	DBC *cursor = NULL;
	DBT pair[2];
	int e, ret = -1;
	char *match;

	memset(&pair[0], 0, sizeof(DBT) * 2);

	if (open_env(&db, PROFILE_DB)) goto out;
	blaa = &db;

	db.profile->cursor(db.profile, NULL, &cursor, 0);

	// FIXME: multiple instance keys?
	match = make_profile_key(node_no, app, key, NULL);
	if (!match) goto out;
	while ((e = cursor->c_get(cursor, &pair[0], &pair[1], DB_NEXT)) == 0) {
		if (strncmp(match, pair[0].data, strlen(match)) == 0)
			func(((char *) pair[0].data) + strlen(match), pair[0].size - strlen(match));
	}
	if (e != DB_NOTFOUND) {
		goto out;
	}

	ret = 0;
out:
	blaa = NULL;
	if (cursor) cursor->c_close(cursor);
	close_env(&db);
	return ret;
}

char *
db_dump_profile(void)
{
	struct databases db;
	struct pack *p;
	DBC *cursor = NULL;
	DBT pair[2];
	int e;
	iks *xml = NULL, *item, *x;
	char *ret = NULL;

	memset(&pair[0], 0, sizeof(DBT) * 2);
	pair[1].flags = DB_DBT_MALLOC;

	if (open_env(&db, PROFILE_DB)) goto out;

	db.profile->cursor(db.profile, NULL, &cursor, 0);

	xml = iks_new("comarProfile");
	iks_insert_cdata(xml, "\n", 1);
	while ((e = cursor->c_get(cursor, &pair[0], &pair[1], DB_NEXT)) == 0) {
		char *t;
		size_t ts;
		item = iks_insert(xml, "item");
		iks_insert_cdata(iks_insert(item, "key"), pair[0].data, pair[0].size);
		p = pack_wrap(pair[1].data, pair[1].size);
		while (pack_get(p, &t, &ts)) {
			iks_insert_cdata(item, "\n", 1);
			x = iks_insert(item, "data");
			iks_insert_attrib(x, "key", t);
			pack_get(p, &t, &ts);
			iks_insert_cdata(iks_insert(x, "value"), t, ts);
		}
		pack_delete(p);
		iks_insert_cdata(xml, "\n", 1);
	}
	if (e != DB_NOTFOUND) {
		goto out;
	}

	ret = iks_string(NULL, xml);
out:
	if (cursor) cursor->c_close(cursor);
	close_env(&db);
	if (xml) iks_delete(xml);
	return ret;
}
