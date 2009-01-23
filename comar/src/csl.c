/*
** Copyright (c) 2005-2007, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <dbus/dbus.h>
#include <Python.h>
#include <node.h>

#include "cfg.h"
#include "csl.h"
#include "data.h"
#include "dbus.h"
#include "log.h"
#include "process.h"
#include "pydbus.h"
#include "utility.h"
#include "model.h"

//! Initializes Python VM
void
csl_init()
{
    Py_Initialize();
}

//! Finalizes Python VM
void
csl_end()
{
    Py_Finalize();
}

static PyObject *
c_i18n(PyObject *self, PyObject *args)
{
    PyObject *dict;
    PyObject *ret = NULL;

    if (!PyArg_ParseTuple(args, "O!", &PyDict_Type, &dict))
        return NULL;

    if (my_proc.locale) {
        ret = PyDict_GetItemString(dict, my_proc.locale);
    }
    if (!ret) {
        ret = PyDict_GetItemString(dict, "en");
    }
    Py_INCREF(ret);
    return ret;
}

//! CSL method: script()
static PyObject *
c_script(PyObject *self, PyObject *args)
{
    /*!
     * This method can be used in CSL scripts to get script's owner.
     *
     * @return Owner of the running CSL script.
     */

    const char *path = dbus_message_get_path(my_proc.bus_msg);
    const char *app = strsub(path, strlen("/package/"), 0);
    return PyString_FromString(app);
}

//! CSL method: call(app, model, method, (arg0, arg1, ...))
static PyObject *
c_call(PyObject *self, PyObject *args)
{
    /*!
     * This method can be used in CSL scripts to call Comar methods
     * internally.
     *
     * @return Called method's reply
     */

    PyObject *ret, *tuple = NULL;
    char *app, *model, *method, *interface, *path;
    int size, i;
    int timeout = -1;

    if (!PyArg_ParseTuple(args, "sss|Oi", &app, &model, &method, &tuple, &timeout))
        return NULL;


    if (!tuple) {
        tuple = PyTuple_New(0);
    }

    if (timeout != -1) {
        timeout = timeout * 1000;
    }

    DBusConnection *conn;
    DBusError err;
    DBusMessage *msg, *reply;
    DBusMessageIter iter;

    dbus_error_init(&err);
    conn = dbus_bus_get_private(DBUS_BUS_SYSTEM, &err);
    if (dbus_error_is_set(&err)) {
        PyErr_SetString(PyExc_Exception, "Unable to open connection for call() method.");
        dbus_error_free(&err);
        return NULL;
    }

    size = strlen(cfg_bus_interface) + 1 + strlen(model) + 1;
    interface = malloc(size);
    snprintf(interface, size, "%s.%s", cfg_bus_interface, model);
    interface[size - 1] = '\0';

    size = strlen("/package/") + strlen(app) + 1;
    path = malloc(size);
    snprintf(path, size, "/package/%s", app);
    path[size - 1] = '\0';

    msg = dbus_message_new_method_call(cfg_bus_name, path, interface, method);
    free(interface);
    free(path);

    dbus_message_iter_init_append(msg, &iter);

    if (PyTuple_Check(tuple)) {
        if (PyTuple_Size(tuple) > 0) {
            for (i = 0; i < PyTuple_Size(tuple); i++) {
                if (dbus_py_export(&iter, PyTuple_GetItem(tuple, i)) != 0) {
                    return NULL;
                }
            }
        }
    }
    else {
        if (dbus_py_export(&iter, tuple) != 0) {
            return NULL;
        }
    }

    reply = dbus_connection_send_with_reply_and_block(conn, msg, timeout, &err);
    dbus_message_unref(msg);
    dbus_connection_close(conn);
    dbus_connection_unref(conn);
    if (dbus_error_is_set(&err)) {
        PyErr_Format(PyExc_Exception, "Unable to call method: %s", err.message);
        dbus_error_free(&err);
        return NULL;
    }

    switch (dbus_message_get_type(reply)) {
        case DBUS_MESSAGE_TYPE_METHOD_RETURN:
            ret = PyList_AsTuple(dbus_py_import(reply));
            if (PyTuple_Size(ret) == 1) {
                ret = PyTuple_GetItem(ret, 0);
            }
            dbus_message_unref(reply);
            return ret;
        case DBUS_MESSAGE_TYPE_ERROR:
            PyErr_SetString(PyExc_Exception, dbus_message_get_error_name(reply));
            dbus_message_unref(reply);
            return NULL;
    }

    Py_INCREF(Py_None);
    return Py_None;
}

//! CSL method: notify(model, signal, message)
static PyObject *
c_notify(PyObject *self, PyObject *args)
{
    /*!
     * This method can be used in CSL scripts to emit DBus signals.
     */
    const char *model, *path, *method;
    char *interface;
    PyObject *tuple;
    int size;

    if (!PyArg_ParseTuple(args, "ssO", &model, &method, &tuple))
        return NULL;

    path = dbus_message_get_path(my_proc.bus_msg);

    size = strlen(cfg_bus_interface) + 1 + strlen(model) + 1;
    interface = malloc(size);
    snprintf(interface, size, "%s.%s", cfg_bus_interface, model);
    interface[size - 1] = '\0';

    if (model_lookup_signal(model, method) != -1) {
        dbus_signal(path, interface, method, tuple);
        free(interface);
        Py_INCREF(Py_None);
        return Py_None;
    }
    else {
        free(interface);
        PyErr_SetString(PyExc_Exception, "Invalid application, model or method.");
        return NULL;
    }
}

//! CSL method: fail(message)
static PyObject *
c_fail(PyObject *self, PyObject *args)
{
    /*!
     * This method can be used in CSL scripts to raise exceptions.
     */

    const char *errstr;
    size_t size;

    if (!PyArg_ParseTuple(args, "s#", &errstr, &size)) {
        return NULL;
    }

    PyErr_SetString(PyExc_Exception, PyString_AsString(PyTuple_GetItem(args, 0)));
    return NULL;
}

//! CSL method: model_apps(model) -> [app, app]
static PyObject *
c_model_apps(PyObject *self, PyObject *args)
{
    /*!
     * This method can be used in CSL scripts to return applications provide that model.
     */

    char *model;

    if (!PyArg_ParseTuple(args, "s", &model)) {
        return NULL;
    }

    if (model_lookup_interface(model) == -1) {
        PyErr_SetString(PyExc_Exception, "No such model.");
        return NULL;
    }

    char *apps;
    PyObject *py_list = PyList_New(0);

    db_get_model_apps(model, &apps);
    if (apps != NULL) {
        char *pch = strtok(apps, "|");
        while (pch != NULL) {
            if (strlen(pch) > 0) {
                PyList_Append(py_list, PyString_FromString(pch));
            }
            pch = strtok(NULL, "|");
        }
        free(apps);
    }

    return py_list;
}

//! CSL method: log_debugmessage)
static PyObject *
c_log_debug(PyObject *self, PyObject *args)
{
    /*!
     * This method can be used in CSL scripts to log debug messages.
     */

    const char *msg;

    if (!PyArg_ParseTuple(args, "s", &msg)) {
        return NULL;
    }

    log_debug(LOG_PROC, "%s\n", msg);

    Py_INCREF(Py_None);
    return Py_None;
}

//! CSL methods
static PyMethodDef methods[] = {
    { "script", c_script, METH_NOARGS, "Return package name" },
    { "_", c_i18n, METH_VARARGS, "Return localized text from a dictionary" },
    { "call", c_call, METH_VARARGS, "Make a syncronous comar call" },
    { "notify", c_notify, METH_VARARGS, "Emits a signal" },
    { "fail", c_fail, METH_VARARGS, "Abort script" },
    { "model_apps", c_model_apps, METH_VARARGS, "List applications registered to model" },
    { "log_debug", c_log_debug, METH_VARARGS, "Logs a debug message" },
    { NULL, NULL, 0, NULL }
};

//! Checks CSL script for errors.
int
py_compile(const char *script_path)
{
    /*!
     * Checks CSL script for errors.
     *
     * @script_path Absolute or relative path of the CSL script.
     * @return 0 on success, 1 on IO errors (missing file, etc.), 2 on script error
     */

    PyObject *pCode;
    char *code = load_file(script_path, NULL);
    if (!code) {
        return 1;
    }

    pCode = Py_CompileString(code, "<script.py>", Py_file_input);
    free(code);
    if (!pCode) {
        return 2;
    }

    return 0;
}

//! Calls model's method with given arguments
int
py_call_method(const char *app, const char *model, const char *method, PyObject *args, PyObject **ret)
{
    /*!
     * Calls model's method with given arguments.
     *
     * @app Application name
     * @model Model
     * @method Method
     * @args Arguments in tuple
     * @ret Value returned by method.
     * @return 0 on success, 1 on IO errors (missing file, etc.), 2 on script error, 3 method is missing.
     */

    PyObject *pCode, *pModule, *pDict, *pFunc;
    PyObject *pkArgs;
    PyMethodDef *meth;

    char *script_path = get_script_path(app, model);
    char *code = load_file(script_path, NULL);
    free(script_path);

    if (!code) {
        return 1;
    }

    pModule = PyImport_AddModule("__builtin__");
    pDict = PyModule_GetDict(pModule);
    for (meth = methods; meth->ml_name; meth++) {
        pCode = PyCFunction_New(meth, NULL);
        PyDict_SetItemString(pDict, meth->ml_name, pCode);
    }

    pCode = Py_CompileString(code, "<script.py>", Py_file_input);
    free(code);
    if (!pCode) {
        return 2;
    }

    pModule = PyImport_ExecCodeModule("csl", pCode);
    Py_DECREF(pCode);

    if (!pModule || !PyModule_Check(pModule)) {
        return 2;
    }

    pDict = PyModule_GetDict(pModule);
    if (!pDict) {
        Py_DECREF(pModule);
        return 2;
    }

    pFunc = PyDict_GetItemString(pDict, method);
    if (!pFunc || !PyCallable_Check(pFunc)) {
        Py_DECREF(pModule);
        return 3;
    }

    if (!PyTuple_Check(args)) {
        PyErr_SetString(PyExc_TypeError, "Arguments must be passed as tuple.");
        return 2;
    }
    pkArgs = PyDict_New();

    *ret = PyObject_Call(pFunc, args, pkArgs);

    if (!*ret) {
        Py_DECREF(pModule);
        return 2;
    }

    Py_DECREF(pModule);
    return 0;
}
