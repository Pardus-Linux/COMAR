/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <Python.h>
#include <marshal.h>
#include <node.h>
#include <compile.h>

#include "csl.h"
#include "process.h"
#include "ipc.h"
#include "notify.h"

static PyObject *
c_call(PyObject *self, PyObject *args)
{
	const char *func;
	size_t size;

	if (!PyArg_ParseTuple(args, "s#", &func, &size))
		return NULL;

	proc_send(TO_PARENT, CMD_CALL, func, size);

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
c_fail(PyObject *self, PyObject *args)
{
	const char *name;
	size_t size;

	if (!PyArg_ParseTuple(args, "s#", &name, &size))
		return NULL;

	// FIXME: fail here :)

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
c_notify(PyObject *self, PyObject *args)
{
	const char *name;
	size_t size;

	if (!PyArg_ParseTuple(args, "s#", &name, &size))
		return NULL;

	notify_fire(name);

	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef methods[] = {
	{ "fail", c_fail, METH_VARARGS, "Abort script and return a fail message" },
	{ "call", c_call, METH_VARARGS, "Call a method from COMAR system model" },
	{ "notify", c_notify, METH_VARARGS, "Send a notification event" },
	{ NULL, NULL, 0, NULL }
};

void
csl_setup(void)
{
	Py_Initialize();
	Py_InitModule("comar", methods);
}

int
csl_compile(char *str, char *name, char **codeptr, size_t *sizeptr)
{
	PyObject *pCode, *pStr;
	node *n;
	size_t size;

	// compile into a code object
	n = PyParser_SimpleParseString(str, Py_file_input);
	if (!n) {
		PyErr_Print();
		return -CSL_BADCODE;
	}
	pCode = (PyObject *) PyNode_Compile(n, name);
	PyNode_Free(n);
	if (!pCode) {
		PyErr_Print();
		return -CSL_BADCODE;
	}

	// serialize code object
#if PY_MINOR_VERSION == 3
	pStr = PyMarshal_WriteObjectToString(pCode);
#else
	pStr = PyMarshal_WriteObjectToString(pCode, 0);
#endif
	Py_DECREF(pCode);
	if (!pStr) {
		return -CSL_NOMEM;
	}
	size = PyString_Size(pStr);
	*codeptr = malloc(size);
	if (!*codeptr) {
		Py_DECREF(pStr);
		return -CSL_NOMEM;
	}
	memcpy(*codeptr, PyString_AsString(pStr), size);
	*sizeptr = size;
	Py_DECREF(pStr);

	return 0;
}

int
csl_execute(char *code, size_t size, const char *func_name, char **resptr, int *reslen)
{
	PyObject *pCode, *pModule, *pDict, *pFunc, *pValue, *pStr;
	PyObject *pArgs, *pkArgs;

	pCode = PyMarshal_ReadObjectFromString(code, size);
	if (!pCode) {
		PyErr_Print();
		return -CSL_BADCODE;
	}
	pModule = PyImport_ExecCodeModule("csl", pCode);
	Py_DECREF(pCode);
	if (!pModule || !PyModule_Check(pModule)) {
		puts("no module");
		return -CSL_BADCODE;
	}

	pDict = PyModule_GetDict(pModule);
	if (!pDict) {
		puts("no dict");
		Py_DECREF(pModule);
		return -CSL_BADCODE;
	}

	pFunc = PyDict_GetItemString(pDict, func_name);
	if (!pFunc || !PyCallable_Check(pFunc)) {
		PyErr_Print();
		Py_DECREF(pModule);
		return -CSL_NOFUNC;
	}

	pArgs = PyTuple_New(0);
	pkArgs = PyDict_New();
	while (1) {
		PyObject *p;
		char *t, *t2;
		size_t sz;
		if (ipc_get_arg(&t, &sz) == 0) break;
		ipc_get_arg(&t2, &sz);
		p = PyString_FromStringAndSize(t2, sz);
		PyDict_SetItemString(pkArgs, t, p);
	}
	pValue = PyObject_Call(pFunc, pArgs, pkArgs);
	if (!pValue) {
		PyErr_Print();
		Py_DECREF(pModule);
		return -CSL_FUNCERR;
	}

	pStr = PyObject_Str(pValue);

	Py_DECREF(pValue);
	Py_DECREF(pModule);

	*reslen = PyString_Size(pStr);
	*resptr = malloc((*reslen) + 1);
	if (!*resptr) {
		Py_DECREF(pStr);
		return -CSL_NOMEM;
	}
	memcpy(*resptr, PyString_AsString(pStr), *reslen);
	(*resptr)[*reslen] = '\0';

	return 0;
}

void
csl_cleanup(void)
{
	Py_Finalize();
}
