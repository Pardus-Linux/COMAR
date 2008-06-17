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

#include "data.h"
#include "cfg.h"
#include "log.h"
#include "utility.h"

//! Database init function
int
db_init(void)
{
    /*!
     * Checks Comar DB directory, creates if not exists.
     *
     * @return 0 on success, -1 on error,
    */

    struct stat fs;
    size_t size;
    char *code_dir;

    if (stat(cfg_data_dir, &fs) != 0) {
        if (0 != mkdir(cfg_data_dir, S_IRWXU)) {
            log_error("Cannot create data dir '%s'\n", cfg_data_dir);
            return -1;
        }
    } else {
        if (0 != access(cfg_data_dir, W_OK)) {
            log_error("Cannot write data dir '%s'\n", cfg_data_dir);
            return -1;
        }
    }

    size = strlen(cfg_data_dir) + 6;
    code_dir = malloc(size);
    if (!code_dir) return -3;
    snprintf(code_dir, size, "%s/code", cfg_data_dir);
    code_dir[size -1] = '\0';
    if (stat(code_dir, &fs) != 0) {
        if (0 != mkdir(code_dir, S_IRWXU)) {
            log_error("Cannot create code dir '%s'\n", code_dir);
            free(code_dir);
            return -1;
        }
    }
    else {
        if (0 != access(code_dir, W_OK)) {
            log_error("Cannot write code dir '%s'\n", code_dir);
            free(code_dir);
            return -1;
        }
    }

    free(code_dir);
    // FIXME: check and recover db files
    return 0;
}

//! Structure that carries databases
struct databases {
    DB_ENV *env;
    DB *app;
    DB *model;
};

#define APP_DB 1
#define MODEL_DB 2

//! Open a database
static int
open_database(DB_ENV *env, DB **dbp, const char *name)
{
    /*!
     * Creates a DB structure that is the handle for a Berkeley DB database
     * and opens it as a standalone, sorted - balanced tree structured DB.
     *
     * @env The environment
     * @dbp DB type
     * @name File name
     * @return 0 on success, -1 if can not create database, -2 if can not open database.
    */

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

//! Creates and open DB_ENV
static int
open_env(struct databases *db, int which)
{
    /*!
     * Creates DB_ENV structure with db_home directory set to
     * comar db dir. After creating enviroment, opens database
     * with created env and specified DB type (type is 'which' in this case)
     *
     * @db Database
     * @which DB type
     * @return 0 on success, -1 if can not create database environment,
     * -2 if can not open database environment, -3 if application db
     * could not be created or opened, -4 if model db could not be
     * created or opened.
     */

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

    if (which & APP_DB) {
        if (open_database(db->env, &db->app, "app.db")) return -3;
    }

    if (which & MODEL_DB) {
        if (open_database(db->env, &db->model, "model.db")) return -4;
    }

    return 0;
}

//! Closes created databases and environment of db
static void
close_env(struct databases *db)
{
    /*
     * @db Database
     */

    if (db->app) db->app->close(db->app, 0);
    if (db->model) db->model->close(db->model, 0);
    db->env->close(db->env, 0);
}

//! Fetches and returns the record called 'name' from database 'db'
static char *
get_data(DB *db, const char *name, size_t *sizep, int *errorp)
{
    /*!
     * Fetches and returns the record called 'name' from database 'db'
     *
     * @db Database
     * @name Key
     * @sizep Size pointer of the value, if requested
     * @errorp Error pointer, if requested
     * @return Keys' value, or NULL if not found
     */

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

//! Puts data to a database
static int
put_data(DB *db, const char *name, const char *data, size_t size)
{
    /*!
     * Puts "name and 'size of name'" as first pair, and
     * "data and size" as second pair to DB.
     *
     * @db Database
     * @name Key
     * @data Value
     * @size Size
     * @return 0 on success, non-zero on error
     */

    DBT pair[2];

    memset(&pair[0], 0, sizeof(DBT) * 2);
    pair[0].data = (char *) name;
    pair[0].size = strlen(name);
    pair[1].data = (char *) data;
    pair[1].size = size;
    return db->put(db, NULL, &pair[0], &pair[1], 0);
}

//! Deletes name from database
static int
del_data(DB *db, const char *name)
{
    /*!
     * Deletes a key from database
     *
     * @db Database
     * @name Key
     * @return 0 on success, non-zero on error
     */

    DBT key;

    memset(&key, 0, sizeof(DBT));
    key.data = (char *) name;
    key.size = strlen(name);
    return db->del(db, NULL, &key, 0);
}

//! Says if database have that key
static int
have_key(DB *db, const char *key)
{
    /*!
     * Says if database have that key
     *
     * @db Database
     * @key Key
     * @return 1 if true, 0 if false
     */

    char *old;
    int e;

    old = get_data(db, key, NULL, &e);

    return old != NULL;
}

//! Says if key have that item in it's value
static int
key_have_item(DB *db, const char *key, const char *item)
{
    /*!
     * Says if key have that item in it's value
     *
     * @db Database
     * @key Key
     * @item Item
     * @return 1 if true, 0 if false
     */

    char *old, *t, *s;
    int e;

    old = get_data(db, key, NULL, &e);

    t = strdup(old);
    if (!t) return -1;
    for (; t; t = s) {
        s = strchr(t, '|');
        if (s) {
            *s = '\0';
            ++s;
        }
        if (strcmp(t, item) == 0) {
            return 1;
        }
    }

    return 0;
}

//! Appends an item to db
static int
append_item(DB *db, const char *key, const char *item)
{
    /*!
     * Appends an item to db
     * @db Database
     * @key Key
     * @item Item
     * @return 0 on success, non-zero on error
     */

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

    if (key_have_item(db, key, item)) return 0;

    // append to old records
    len = strlen(old) + 1 + strlen(item) + 1;
    data = malloc(len);
    if (!data) return -1;
    snprintf(data, len, "%s|%s", old, item);

    e = put_data(db, key, data, strlen(data) + 1);
    if (e) return -1;

    return 0;
}

//! Returns script path of a registered application&model pair
char *
get_script_path(const char *app, const char *model)
{
    /*!
     * Returns script path of a registered application&model pair
     *
     * @app Application
     * @model Model
     * @return Script path
     */

    char *realpath, *model_escaped;
    int size;

    size = strlen(cfg_data_dir) + 1 + strlen("code") + 1 + strlen(model) + 1 + strlen(app) + 4;
    realpath = malloc(size);

    model_escaped = (char *) strrep(model, '.', '_');

    // Generate script path
    snprintf(realpath, size, "%s/code/%s_%s.py", cfg_data_dir, model_escaped, app);
    realpath[size - 1] = '\0';
    free(model_escaped);
    return realpath;
}

//! Registers an application model
int
db_register_model(char *app, char *model)
{
    /*
     * Appends application to index "__app__", and model to app's index.
     *
     * @app Application
     * @model Model
     * @return 0 on success, non-zero on error
     */

    struct databases db;
    int ret = 0;

    if (open_env(&db, APP_DB | MODEL_DB)) goto out;

    ret = append_item(db.app, app, model);
    if (ret) goto out;
    ret = append_item(db.app, "__apps__", app);
    if (ret) goto out;

    ret = append_item(db.model, model, app);
    if (ret) goto out;

out:
    close_env(&db);
    return ret;
}

//! Removes application
int
db_remove_app(char *app)
{
    /*
     * Removes application from index "__app__" and remove app's index.
     *
     * @app Application
     * @return 0 on success, non-zero on error
     */

    struct databases db;
    char *list, *list2, *t, *s;
    char *list_models, *list_apps;
    char *app_rem;
    int ret = 0;
    int size;

    size = strlen(app) + 2;
    app_rem = malloc(size);
    snprintf(app_rem, size, "%s|", app);
    app_rem[size - 1] = '\0';

    if (open_env(&db, APP_DB | MODEL_DB)) goto out;

    list = get_data(db.app, app, NULL, &ret);
    if (!list) goto out;

    size = strlen(list) + 2;
    list_models = malloc(size);
    snprintf(list_models, size, "%s|", list);
    list_models[size - 1] = '\0';
    free(list);

    // iterate over app's models
    for (t = list_models; t; t = s) {
        s = strchr(t, '|');
        if (s) {
            *s = '\0';
            ++s;
        }

        // remove app from model's application list in model.db
        list2 = get_data(db.model, t, NULL, &ret);
        if (list2) {
            size = strlen(list2) + 2;
            list_apps = malloc(size);
            snprintf(list_apps, size, "%s|", list2);
            list_apps[size - 1] = '\0';
            free(list2);

            char *k;
            int sa = strlen(app_rem);
            k = strstr(list_apps, app_rem);
            if (k) {
                if (k[sa] == '|') ++sa;
                memmove(k, k + sa, strlen(k) - sa + 1);
                sa = strlen(list_apps);
                if (sa > 0) {
                    if (list_apps[sa-1] == '|')
                        list_apps[sa-1] = '\0';
                }
                ret = put_data(db.model, t, list_apps, strlen(list_apps) + 1);
                if (ret) goto out;
            }
            free(list_apps);
        }
    }
    free(list_models);

    // remove app from application list in app.db
    list = get_data(db.app, "__apps__", NULL, &ret);
    size = strlen(list) + 2;
    list_apps = malloc(size);
    snprintf(list_apps, size, "%s|", list);
    list_apps[size - 1] = '\0';
    free(list);

    if (list_apps) {
        char *k;
        int sa = strlen(app_rem);
        k = strstr(list_apps, app_rem);
        if (k) {
            if (k[sa] == '|') ++sa;
            memmove(k, k + sa, strlen(k) - sa + 1);
            sa = strlen(list_apps);
            if (sa > 0) {
                if (list_apps[sa-1] == '|')
                    list_apps[sa-1] = '\0';
            }
            ret = put_data(db.app, "__apps__", list_apps, strlen(list_apps) + 1);
            if (ret) goto out;
        }
    }
    free(list_apps);
    free(app_rem);

    ret = del_data(db.app, app);
    if (ret) goto out;

out:
    close_env(&db);
    return ret;
}

//! Returns installed applications
int
db_get_apps(char **bufferp)
{
    /*
     * Exports installed application list.
     *
     * @bufferp Pointer to contain list
     * @return 0 on success, non-zero on error
     */

    struct databases db;
    int ret = -1;

    if (open_env(&db, APP_DB)) goto out;

    *bufferp = get_data(db.app, "__apps__", NULL, &ret);

out:
    close_env(&db);
    return ret;
}

//! Returns application's models
int
db_get_app_models(char *app, char **bufferp)
{
    /*
     * Exports application's models.
     *
     * @app Application
     * @bufferp Pointer to contain list
     * @return 0 on success, non-zero on error
     */

    struct databases db;
    int ret = -1;

    if (open_env(&db, APP_DB)) goto out;

    *bufferp = get_data(db.app, app, NULL, &ret);

out:
    close_env(&db);
    return ret;
}

//! Returns application have specified model
int
db_get_model_apps(char *model, char **bufferp)
{
    /*
     * Exports applications that have specified model.
     *
     * @model Model
     * @bufferp Pointer to contain list
     * @return 0 on success, non-zero on error
     */

    struct databases db;
    int ret = -1;

    if (open_env(&db, MODEL_DB)) goto out;

    *bufferp = get_data(db.model, model, NULL, &ret);

out:
    close_env(&db);
    return ret;
}

//! Checks if application is registered
int
db_check_app(char *app)
{
    /*
     * Checks if application is registered.
     *
     * @app Application
     * @return 1 if true, 0 if false
     */

    struct databases db;
    int ret = 0;

    if (open_env(&db, APP_DB)) goto out;

    ret = have_key(db.app, app);
out:
    close_env(&db);
    return ret;
}

//! Check if application has model
int
db_check_model(char *app, char *model)
{
    /*
     * Check if application has model
     *
     * @app Application
     * @model Model
     * @return 1 if true, 0 if false
     */

    struct databases db;
    int ret = 0;

    if (open_env(&db, APP_DB)) goto out;

    ret = have_key(db.app, app);
    if (!ret) goto out;

    ret = key_have_item(db.app, app, model);
out:
    close_env(&db);
    return ret;
}
