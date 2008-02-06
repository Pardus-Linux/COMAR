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
    PyObject *ret;

    if (!PyArg_ParseTuple(args, "O!", &PyDict_Type, &dict))
        return NULL;

    ret = PyDict_GetItemString(dict, "en");
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

    PyObject *tuple = NULL;
    PyObject *result;
    char *app, *model, *method;
    int ret;

    if (!PyArg_ParseTuple(args, "sss|O", &app, &model, &method, &tuple))
        return NULL;


    if (!tuple) {
        tuple = PyTuple_New(0);
    }

    if (db_check_model(app, model) && model_lookup_method(model, method) != -1) {
        ret = py_call_method(app, model, method, tuple, &result);

        if (ret == 0) {
            return result;
        }
        else if (ret == 1) {
            PyErr_SetString(PyExc_Exception, "Internal error, unable to find script.");
        }
        return NULL;
    }
    else {
        PyErr_SetString(PyExc_Exception, "Invalid application, model or method.");
        return NULL;
    }
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

//! CSL methods
static PyMethodDef methods[] = {
    { "script", c_script, METH_NOARGS, "Return package name" },
    { "_", c_i18n, METH_VARARGS, "Return localized text from a dictionary" },
    { "call", c_call, METH_VARARGS, "Make a syncronous comar call" },
    { "notify", c_notify, METH_VARARGS, "Emits a signal" },
    { "fail", c_fail, METH_VARARGS, "Abort script" },
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
