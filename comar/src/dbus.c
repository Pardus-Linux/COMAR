/*
** Copyright (c) 2005-2007, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <Python.h>
#include <stdlib.h>
#include <sys/poll.h>
#include <dbus/dbus.h>
#include <unistd.h>

#include "cfg.h"
#include "csl.h"
#include "data.h"
#include "iksemel.h"
#include "log.h"
#include "model.h"
#include "policy.h"
#include "process.h"
#include "pydbus.h"
#include "utility.h"

#define MAX_CHILDREN 1000
#define MAX_WATCHES 10
#define MAX_FDS (MAX_CHILDREN + MAX_WATCHES)

static struct pollfd pollfds[MAX_WATCHES];
static DBusWatch *watches[MAX_WATCHES];
static int n_watches = 0;

//! Sends message to client
void
dbus_send(DBusMessage *reply)
{
    /*
     * Sends DBus message to client.
     *
     * @reply DBus message to be sent
     */

    dbus_uint32_t serial = 0;

    if (!dbus_connection_send(my_proc.bus_conn, reply, &serial)) {
        log_error("Out Of Memory!\n");
        proc_finish();
    }

    dbus_connection_flush(my_proc.bus_conn);
    dbus_message_unref(reply);
}

//! Creates an error message and sends
static void
dbus_reply_error(char *class, char *name, char *str)
{
    /*
     * Creates an error message and sends to client. Does nothing if client
     * ignores reply.
     *
     * @str Message
     */

    if (dbus_message_get_no_reply(my_proc.bus_msg)) return;

    char *err_name;
    int size;

    size = strlen(cfg_bus_interface) + 1 + strlen(class) + 1 + strlen(name) + 1;
    err_name = malloc(size);
    snprintf(err_name, size, "%s.%s.%s", cfg_bus_interface, class, name);
    err_name[size - 1] = '\0';

    DBusMessage *reply = dbus_message_new_error(my_proc.bus_msg, err_name, str);
    dbus_send(reply);
    free(err_name);
}

//! Logs a Python exception
static void
log_exception()
{
    /*
     * Logs a Python exception and sends reply to the client.
     */

    PyObject *pType;
    PyObject *pValue;
    PyObject *pTrace;
    char *eStr;
    char *vStr = "";
    long lineno = 0;

    PyErr_Fetch(&pType, &pValue, &pTrace);
    if (!pType) {
        log_error("log_exception() called when there isn't an exception\n");
        return;
    }

    eStr = PyString_AsString(PyObject_Str(pType));

    if (pValue) {
        PyObject *tmp;
        tmp = PyObject_Str(pValue);
        if (tmp) vStr = PyString_AsString(tmp);
    }

    if (pTrace) {
        PyObject *tmp;
        tmp = PyObject_GetAttrString(pTrace, "tb_lineno");
        if (tmp) lineno = PyInt_AsLong(tmp);
    }

    log_error("Python Exception [%s] in (%s,%s,%ld): %s\n", eStr, dbus_message_get_interface(my_proc.bus_msg), dbus_message_get_path(my_proc.bus_msg), lineno, vStr);

    dbus_reply_error("python", eStr, vStr);
}

//! Emits a signal
void
dbus_signal(const char *path, const char *interface, const char *name, PyObject *obj)
{
    /*
     * Emits a DBus signal.
     * 
     * @path Object path
     * @interface Interface
     * @name Signal name
     * @obj Arguments (Python object)
     */

    DBusMessage *msg;
    DBusMessageIter iter;

    msg = dbus_message_new_signal(path, interface, name);
    dbus_message_iter_init_append(msg, &iter);
    if (obj != Py_None) {
        if (PyTuple_Check(obj)) {
            int i;
            for (i = 0; i < PyTuple_Size(obj); i++) {
                if (dbus_py_export(&iter, PyTuple_GetItem(obj, i)) != 0) {
                    log_exception();
                }
            }
        }
        else {
            if (dbus_py_export(&iter, obj) != 0) {
                log_exception();
            }
        }
    }

    dbus_send(msg);
}

//! Creates a message from Python object and sends
static void
dbus_reply_object(PyObject *obj)
{
    /*
     * Creates a DBus message from Python object and sends to client. 
     * Does nothing if client ignores reply.
     *
     * @obj Python object
     */

    if (dbus_message_get_no_reply(my_proc.bus_msg)) return;

    DBusMessage *reply;
    DBusMessageIter iter;

    reply = dbus_message_new_method_return(my_proc.bus_msg);
    dbus_message_iter_init_append(reply, &iter);
    if (obj != Py_None) {
        if (PyTuple_Check(obj)) {
            int i;
            for (i = 0; i < PyTuple_Size(obj); i++) {
                if (dbus_py_export(&iter, PyTuple_GetItem(obj, i)) != 0) {
                    log_exception();
                }
            }
        }
        else {
            if (dbus_py_export(&iter, obj) != 0) {
                log_exception();
            }
        }
    }
    dbus_send(reply);
}

//! Creates a message and sends
static void
dbus_reply_str(char *str)
{
    /*
     * Creates a DBus message from string and sends to client.
     * Does nothing if client ignores reply.
     *
     * @str Message
     */

    if (dbus_message_get_no_reply(my_proc.bus_msg)) return;

    DBusMessage *reply;
    DBusMessageIter iter;
    reply = dbus_message_new_method_return(my_proc.bus_msg);
    dbus_message_iter_init_append(reply, &iter);
    dbus_message_iter_append_basic(&iter, DBUS_TYPE_STRING, &str);
    dbus_send(reply);
}

//! Creates introspection for given object path
static void
dbus_introspection_methods(const char *path)
{
    /*
     * Creates introspection XML for given object path and sends to client.
     *
     * @path Object path
     */

    if (strcmp(path, "/") == 0) {
        iks *xml = iks_new("node");

        // package node contains applications and models
        iks_insert_attrib(iks_insert(xml, "node"), "name", "package");

        // add standard interfaces
        model_get_iks("org.freedesktop.DBus.Introspectable", &xml);

        // add core interface
        model_get_iks("Comar", &xml);

        dbus_reply_str(iks_string(NULL, xml));
        iks_delete(xml);
    }
    else if (strcmp(path, "/package") == 0) {
        char *apps;
        db_get_apps(&apps);
        if (apps == NULL) {
            iks *xml = iks_new("node");

            // add standard interfaces
            model_get_iks("org.freedesktop.DBus.Introspectable", &xml);

            dbus_reply_str(iks_string(NULL, xml));
            iks_delete(xml);
        }
        else {
            iks *xml = iks_new("node");
            char *pch = strtok(apps, "|");
            while (pch != NULL) {
                if (strlen(pch) > 0) {
                    iks_insert_attrib(iks_insert(xml, "node"), "name", pch);
                }
                pch = strtok(NULL, "|");
            }

            // add standard interfaces
            model_get_iks("org.freedesktop.DBus.Introspectable", &xml);

            dbus_reply_str(iks_string(NULL, xml));
            iks_delete(xml);
            free(apps);
        }
    }
    else if (strncmp(path, "/package/", strlen("/package/")) == 0) {
        char *app = (char *) strsub(path, strlen("/package/"), 0);
        if (!db_check_app(app)) {
            log_error("No such application: '%s'\n", app);
            dbus_reply_error("db", "noapp", "No such application.");
        }
        else {
            char *models;
            db_get_app_models(app, &models);
            if (models == NULL) {
                iks *xml = iks_new("node");

                // add standard interfaces
                model_get_iks("org.freedesktop.DBus.Introspectable", &xml);

                dbus_reply_str(iks_string(NULL, xml));
                iks_delete(xml);
            }
            else {
                iks *xml = iks_new("node");
                char *pch = strtok(models, "|");
                while (pch != NULL) {
                    if (strlen(pch) > 0) {
                        model_get_iks(pch, &xml);
                    }
                    pch = strtok(NULL, "|");
                }

                // add standard interfaces
                model_get_iks("org.freedesktop.DBus.Introspectable", &xml);

                dbus_reply_str(iks_string(NULL, xml));
                iks_delete(xml);
                free(models);
            }
        }
        free(app);
    }
    else {
        log_error("Unknown object path '%s'\n", path);
        dbus_reply_error("dbus", "unknownpath", "Object path unknown.");
    }
}

//! Replies messages made to COMAR core interface
static void
dbus_comar_methods(const char *method)
{
    /*
     * Replies messages made to COMAR core interface.
     * Methods in COMAR core are:
     *     listApplications()
     *     listModels()
     *     listApplicationModels(app)
     *     register(app, model, script)
     *     remove(app)
     *
     * @method Method
     */

    PyObject *args, *result;
    char *app, *model, *script, *apps, *models, *code;

    if (strcmp(method, "listApplications") == 0) {
        db_get_apps(&apps);
        result = PyList_New(0);
        if (apps != NULL) {
            char *pch = strtok(apps, "|");
            while (pch != NULL) {
                if (strlen(pch) > 0) {
                    PyList_Append(result, PyString_FromString(pch));
                }
                pch = strtok(NULL, "|");
            }
            free(apps);
        }
        dbus_reply_object(result);
    }
    else if (strcmp(method, "listModels") == 0) {
        result = PyList_New(0);
        iks *obj;
        for (obj = iks_first_tag(model_xml); obj; obj = iks_next_tag(obj)) {
            if (iks_strcmp(iks_find_attrib(obj, "name"), "Comar") == 0 || iks_strncmp(iks_find_attrib(obj, "name"), "org.freedesktop.", strlen("org.freedesktop.")) == 0) {
                continue;
            }
            PyList_Append(result, PyString_FromString(iks_find_attrib(obj, "name")));
        }
        dbus_reply_object(result);
    }
    else if (strcmp(method, "listModelApplications") == 0) {
        args = dbus_py_import(my_proc.bus_msg);
        model = PyString_AsString(PyList_GetItem(args, 0));
        if (model_lookup_interface(model) == -1) {
            log_error("No such model: '%s'\n", model);
            dbus_reply_error("db", "nomodel", "No such model.");
            return;
        }
        db_get_model_apps(model, &apps);
        if (apps != NULL) {
            result = PyList_New(0);
            char *pch = strtok(apps, "|");
            while (pch != NULL) {
                if (strlen(pch) > 0) {
                    PyList_Append(result, PyString_FromString(pch));
                }
                pch = strtok(NULL, "|");
            }
            dbus_reply_object(result);
            free(apps);
        }
        else {
            result = PyList_New(0);
            dbus_reply_object(result);
        }
    }
    else if (strcmp(method, "listApplicationModels") == 0) {
        args = dbus_py_import(my_proc.bus_msg);
        app = PyString_AsString(PyList_GetItem(args, 0));
        db_get_app_models(app, &models);
        if (models != NULL) {
            result = PyList_New(0);
            char *pch = strtok(models, "|");
            while (pch != NULL) {
                if (strlen(pch) > 0) {
                    PyList_Append(result, PyString_FromString(pch));
                }
                pch = strtok(NULL, "|");
            }
            dbus_reply_object(result);
            free(models);
        }
        else {
            result = PyList_New(0);
            dbus_reply_object(result);
        }
    }
    else if (strcmp(method, "register") == 0) {
        args = dbus_py_import(my_proc.bus_msg);
        app = PyString_AsString(PyList_GetItem(args, 0));
        model = PyString_AsString(PyList_GetItem(args, 1));
        script = PyString_AsString(PyList_GetItem(args, 2));

        if (model_lookup_interface(model) == -1) {
            log_error("No such model: '%s'\n", model);
            dbus_reply_error("db", "nomodel", "No such model.");
        }
        else {
            if (py_compile(script) != 0) {
                log_error("Not a valid Python script: '%s'\n", script);
                dbus_reply_error("python", "SyntaxError", "Not a valid Python script.");
            }
            else {
                code = load_file(script, NULL);
                script = get_script_path(app, model);
                save_file(script, code, strlen(code));
                free(script);
                db_register_model(app, model);
                dbus_reply_object(PyBool_FromLong(1));
            }
        }
    }
    else if (strcmp(method, "remove") == 0) {
        args = dbus_py_import(my_proc.bus_msg);
        app = PyString_AsString(PyList_GetItem(args, 0));
        db_get_app_models(app, &models);

        if (models == NULL) {
            dbus_reply_object(PyBool_FromLong(0));
        }
        else {
            db_remove_app(app);

            char *pch = strtok(models, "|");
            while (pch != NULL) {
                if (strlen(pch) > 0) {
                    script = get_script_path(app, pch);
                    unlink(script);
                    //free(script);
                }
                pch = strtok(NULL, "|");
            }

            dbus_reply_object(PyBool_FromLong(1));
        }
    }
    else {
        log_error("Unknown method: '%s'\n", method);
        dbus_reply_error("dbus", "unknownmethod", "Unknown method");
    }
}

//! Replies messages made to registered application models
void
dbus_app_methods(const char *interface, const char *path, const char *method)
{
    /*
     * Replies messages made to registered application models.
     * Extracts method arguments from DBus Message (reachable via my_proc.bus_msg)
     *
     * @interface Interface
     * @path Object path
     * @method Method
     */

    PyObject *args, *result;
    int ret;

    char *app = (char *) strsub(path, strlen("/package/"), 0);
    char *model = (char *) strsub(interface, strlen(cfg_bus_interface) + 1, 0);

    if (!db_check_model(app, model)) {
        log_error("Application interface doesn't exist: %s (%s)\n", model, app);
        dbus_reply_error("dbus", "unknownmodel", "Application interface doesn't exist.");
    }
    else if (model_lookup_method(model, method) == -1) {
        log_error("Unknown method: %s.%s\n", model, method);
        dbus_reply_error("dbus", "unknownmethod", "Unknown method.");
    }
    else {
        args = PyList_AsTuple(dbus_py_import(my_proc.bus_msg));
        ret = py_call_method(app, model, method, args, &result);

        if (ret == 1) {
            log_error("Unable to find: %s (%s)\n", model, app);
            dbus_reply_error("core", "internal", "Unable to find script.");
        }
        else if (ret == 2) {
            log_exception();
        }
        else if (ret == 3) {
            log_error("Unable to find '%s' method in script: %s (%s)\n", method, model, app);
            dbus_reply_error("python", "missing", "Method is not defined in script.");
        }
        else {
            dbus_reply_object(result);
        }
    }
    free(app);
    free(model);
}

//! Checks if sender is allowed to call specified method
static int
dbus_policy_check(const char *sender, const char *interface, const char *method)
{
    /*!
     *
     * @sender Bus name of the sender
     * @interface Interface
     * @method Method
     * @return 1 if access granted, 0 if access denied
     */

    PolKitResult polkit_result;

    if (policy_check(sender, interface, method, &polkit_result)) {
        log_debug(LOG_PLCY, "PolicyKit: %s.%s = %s\n", interface, method, polkit_result_to_string_representation(polkit_result));
        switch (polkit_result) {
            case POLKIT_RESULT_YES:
            case POLKIT_RESULT_N_RESULTS:
                return 1;
            case POLKIT_RESULT_UNKNOWN:
            case POLKIT_RESULT_NO:
                dbus_reply_error("policy", "no", "Access denied.");
                return 0;
            case POLKIT_RESULT_ONLY_VIA_ADMIN_AUTH:
            case POLKIT_RESULT_ONLY_VIA_ADMIN_AUTH_KEEP_SESSION:
            case POLKIT_RESULT_ONLY_VIA_ADMIN_AUTH_KEEP_ALWAYS:
            case POLKIT_RESULT_ONLY_VIA_ADMIN_AUTH_ONE_SHOT:
                dbus_reply_error("policy", "auth_admin", "Access denied, but can be granted via admin auth.");
                return 0;
            case POLKIT_RESULT_ONLY_VIA_SELF_AUTH:
            case POLKIT_RESULT_ONLY_VIA_SELF_AUTH_KEEP_SESSION:
            case POLKIT_RESULT_ONLY_VIA_SELF_AUTH_KEEP_ALWAYS:
            case POLKIT_RESULT_ONLY_VIA_SELF_AUTH_ONE_SHOT:
                dbus_reply_error("policy", "auth_self", "Access denied, but can be granted via self auth.");
                return 0;
        }
    }
    dbus_reply_error("core", "internal", "Unable to query PolicyKit");
    return 0;
}

//! Forked function that handles method calls
static void
dbus_method_call()
{
    /*
     * This function handles method calls.
     *
     * DBus connection is reacable via my_proc.bus_conn
     * DBus message is reacable via my_proc.bus_msg
     *
     */

    struct timeval time_start, time_end;
    unsigned long msec;

    const char *interface = dbus_message_get_interface(my_proc.bus_msg);
    const char *path = dbus_message_get_path(my_proc.bus_msg);
    const char *method = dbus_message_get_member(my_proc.bus_msg);
    const char *sender = dbus_message_get_sender(my_proc.bus_msg);

    gettimeofday(&time_start, NULL);

    csl_init();

    if (!interface || !path || !method) {
        dbus_reply_error("dbus", "missing", "Missing interface, path or method.");
    }
    else if (strcmp(interface, "org.freedesktop.DBus.Introspectable") == 0) {
        dbus_introspection_methods(path);
    }
    else if (strncmp(interface, cfg_bus_interface, strlen(cfg_bus_interface)) == 0) {
        if (dbus_policy_check(sender, interface, method)) {
            if (strcmp(path, "/") == 0 && strcmp(interface, cfg_bus_interface) == 0) {
                dbus_comar_methods(method);
            }
            else if (strncmp(path, "/package/", strlen("/package/")) == 0) {
                dbus_app_methods(interface, path, method);
            }
            else {
                log_error("Unknown object path '%s'\n", path);
                dbus_reply_error("dbus", "unknownpath", "Unknown object path");
            }
        }
    }
    else {
        dbus_reply_error("dbus", "unknownmodel", "Unknown interface");
    }

    gettimeofday(&time_end, NULL);
    msec = time_diff(&time_start, &time_end);
    if (msec / 1000 > 60) {
        log_info("Execution of %s.%s (%s) took %.3f seconds\n", interface, method, path, (float) msec / 1000);
    }
    else {
        log_debug(LOG_PERF, "Execution of %s.%s (%s) took %.3f seconds\n", interface, method, path, (float) msec / 1000);
    }

    csl_end();
}

//! Message handler
static DBusHandlerResult
filter_func(DBusConnection *conn, DBusMessage *msg, void *data)
{
    const char *sender = dbus_message_get_sender(msg);
    const char *interface = dbus_message_get_interface(msg);
    const char *method = dbus_message_get_member(msg);

    switch (dbus_message_get_type(msg)) {
        case DBUS_MESSAGE_TYPE_METHOD_CALL:
            log_debug(LOG_DBUS, "DBus method call [%s.%s] from [%s]\n", interface, method, sender);
            proc_fork(dbus_method_call, "ComarJob", conn, msg);
            break;
        case DBUS_MESSAGE_TYPE_SIGNAL:
            log_debug(LOG_DBUS, "DBus signal [%s.%s] from [%s]\n", interface, method, sender);
            break;
    }

    return DBUS_HANDLER_RESULT_HANDLED;
}


static void fd_handler(DBusConnection *conn, short events, DBusWatch *watch)
{
    unsigned int flags = 0;

    if (events & POLLIN)
        flags |= DBUS_WATCH_READABLE;
    if (events & POLLOUT)
        flags |= DBUS_WATCH_WRITABLE;
    if (events & POLLHUP)
        flags |= DBUS_WATCH_HANGUP;
    if (events & POLLERR)
        flags |= DBUS_WATCH_ERROR;

    while (!dbus_watch_handle(watch, flags)) {
        printf("dbus_watch_handle needs more memory\n");
        sleep(1);
    }

    dbus_connection_ref(conn);
    while (dbus_connection_dispatch(conn) == DBUS_DISPATCH_DATA_REMAINS);
    dbus_connection_unref(conn);
}

static dbus_bool_t add_watch(DBusWatch *watch, void *data)
{
    short cond = POLLHUP | POLLERR;
    int fd;
    unsigned int flags;

    //printf("add watch %p\n", (void*)watch);
    fd = dbus_watch_get_unix_fd(watch);
    flags = dbus_watch_get_flags(watch);

    if (flags & DBUS_WATCH_READABLE)
        cond |= POLLIN;
    if (flags & DBUS_WATCH_WRITABLE)
        cond |= POLLOUT;

    pollfds[n_watches].fd = fd;
    pollfds[n_watches].events = cond;
    watches[n_watches] = watch;
    ++n_watches;

    return 1;
}

static void remove_watch(DBusWatch *watch, void *data)
{
    int i, found = 0;

    // printf("remove watch %p\n", (void*)watch);
    for (i = 0; i < n_watches; ++i) {
        if (watches[i] == watch) {
            found = 1;
            break;
        }
    }
    if (!found) {
        printf("watch %p not found\n", (void*)watch);
        return;
    }

    memset(&pollfds[i], 0, sizeof(pollfds[i]));
    watches[i] = NULL;

    if (i == n_watches && n_watches > 0) --n_watches;
}


//! Starts a server and listens for calls/signals
void
dbus_listen()
{
    /*
     * Starts a DBus server and listens for calls and signals.
     * Forks "dbus_method_call" when a method call is fetched.
     */

    DBusConnection *conn;
    DBusError err;
    const char *unique_name;

    dbus_error_init(&err);
    conn = dbus_connection_open_private(cfg_bus_socket, &err);
    if (dbus_error_is_set(&err)) {
        log_error("Connection Error (%s)\n", err.message);
        dbus_error_free(&err);
        return;
    }

    if (!dbus_bus_register(conn, &err)) {
        log_error("Register Error (%s)\n", err.message);
        dbus_error_free(&err);
        goto out;
    }

    dbus_bus_request_name(conn, cfg_bus_name, DBUS_NAME_FLAG_REPLACE_EXISTING, &err);
    if (dbus_error_is_set(&err)) {
        log_error("Name Error (%s)\n", err.message);
        dbus_error_free(&err);
        goto out;
    }

    if (!dbus_connection_set_watch_functions(conn, add_watch, remove_watch, NULL, NULL, NULL)) {
        log_error("dbus_connection_set_watch_functions failed\n");
        goto out;
    }

    if (!dbus_connection_add_filter(conn, filter_func, NULL, NULL)) {
        log_error("Failed to register signal handler callback\n");
        goto out;
    }

    dbus_bus_add_match(conn, "type='method_call'", NULL);

    unique_name = dbus_bus_get_unique_name(conn);
    log_info("Listening on %s (%s)...\n", cfg_bus_name, unique_name);

    while (1) {
        struct pollfd fds[MAX_FDS];
        DBusWatch *watch[MAX_WATCHES];
        int nfds, nfds_w, nfds_c, ret, i, j;

        nfds = 0;
        for (i = 0; i < n_watches; i++) {
            if (pollfds[i].fd == 0 || !dbus_watch_get_enabled(watches[i])) {
                continue;
            }

            fds[nfds].fd = pollfds[i].fd;
            fds[nfds].events = pollfds[i].events;
            fds[nfds].revents = 0;
            watch[nfds] = watches[i];
            nfds++;
            if (i > MAX_WATCHES) {
                printf("ERR: %d watches reached\n", MAX_WATCHES);
                break;
            }
        }
        nfds_w = nfds;

        for (i = 0; i < my_proc.nr_children; i++) {
            fds[nfds].fd = my_proc.children[i].from;
            fds[nfds].events = 0;
            fds[nfds].revents = 0;
            nfds++;
            if (i > MAX_CHILDREN) {
                printf("ERR: %d children reached\n", MAX_CHILDREN);
                break;
            }
        }
        nfds_c = nfds - nfds_w;

        if (cfg_timeout == 0) {
            ret = poll(fds, nfds, -1);
        }
        else {
            ret = poll(fds, nfds, cfg_timeout * 1000);
        }
        if (ret == 0) {
            if (cfg_timeout != 0 && my_proc.nr_children == 0) {
                log_info("Service was idle for more than %d second(s), closing daemon...\n", cfg_timeout);
                shutdown_activated = 1;
                break;
            }
            continue;
        }
        else if (ret < 0) {
            if (shutdown_activated) {
                log_info("Shutdown requested.\n");
            }
            else {
                perror("Poll");
            }
            break;
        }

        for (i = 0; i < nfds_c; i++) {
            for (j = 0; j < my_proc.nr_children; j++) {
                if (my_proc.children[j].from == fds[nfds_w + i].fd) {
                    if (fds[nfds_w + i].revents) {
                        rem_child(j);
                    }
                    break;
                }
            }
        }

        for (i = 0; i < nfds_w; i++) {
            if (fds[i].revents) {
                fd_handler(conn, fds[i].revents, watch[i]);
            }
        }
    }

out:
    dbus_connection_close(conn);
    dbus_connection_unref(conn);
}
