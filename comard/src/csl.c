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

static PyObject *
c_call(PyObject *self, PyObject *args)
{
	const char *func;
	size_t size;

	if (!PyArg_ParseTuple(args, "s#", &func, &size))
		return NULL;

	proc_send_cmd(TO_PARENT, CMD_CALL, size);
	proc_send_data(TO_PARENT, func, size);

	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef methods[] = {
	{ "call", c_call, METH_VARARGS, "Call a method from COMAR system model" },
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
	pStr = PyMarshal_WriteObjectToString(pCode);
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

	pValue = PyObject_CallObject(pFunc, NULL);
	if (!pValue) {
		PyErr_Print();
		Py_DECREF(pModule);
		return -CSL_FUNCERR;
	}

	pStr = PyObject_Str(pValue);

	Py_DECREF(pValue);
	Py_DECREF(pModule);

	*reslen = PyString_Size(pStr);
	*resptr = malloc(*reslen);
	if (!*resptr) {
		Py_DECREF(pStr);
		return -CSL_NOMEM;
	}
	memcpy(*resptr, PyString_AsString(pStr), *reslen);

	return 0;
}

void
csl_cleanup(void)
{
	Py_Finalize();
}
