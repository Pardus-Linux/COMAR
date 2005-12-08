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
#include "log.h"
#include "model.h"
#include "data.h"
#include "utility.h"

// FIXME: cleanup
int job_send_result(int cmd, const char *data, size_t size);
extern int bk_node;
extern char *bk_app;


static PyObject *
c_fail(PyObject *self, PyObject *args)
{
	const char *errstr;
	size_t size;

	if (!PyArg_ParseTuple(args, "s#", &errstr, &size))
		return NULL;

	job_send_result(CMD_FAIL, errstr, size);
	proc_finish();
	// process terminated at this point

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
c_notify(PyObject *self, PyObject *args)
{
	const char *name, *msg;
	size_t size, msize;

	if (!PyArg_ParseTuple(args, "s#s#", &name, &size, &msg, &msize))
		return NULL;

	notify_fire(name, msg);

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *c_instances_list;

static void
c_instances_adder(char *str, size_t size)
{
	PyObject *p;

	p = PyString_FromStringAndSize(str, size);
	PyList_Append(c_instances_list, p);
}

static PyObject *
c_instances(PyObject *self, PyObject *args)
{
	const char *key = NULL;
	char *app;

	c_instances_list = PyList_New(0);

	if (!PyArg_ParseTuple(args, "s", &key))
		return NULL;

	// FIXME: no global instances for now, handle nicely in model.xml
	//if (model_package_profile(bk_node))
		app = bk_app;
	//else
	//	app = NULL;

	db_get_instances(bk_node, app, key, c_instances_adder);

	return c_instances_list;
}

static PyObject *
c_get_profile(PyObject *self, PyObject *args)
{
	struct pack *p;
	const char *node = NULL;
	char *app;
	int node_no;
	char *t;
	size_t ts;
	PyObject *dict;

	dict = PyDict_New();

	if (!PyArg_ParseTuple(args, "|s", &node))
		return NULL;

	if (node)
		node_no = model_lookup_method(node);
	else
		node_no = bk_node;

	if (model_package_profile(node_no))
		app = bk_app;
	else
		app = NULL;

	p = db_get_profile(node_no, app, NULL, NULL);
	if (!p) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	while (pack_get(p, &t, &ts)) {
		PyObject *val;
		char *t2;
		pack_get(p, &t2, &ts);
		val = PyString_FromStringAndSize(t2, ts);
		PyDict_SetItemString(dict, t, val);
	}

	return dict;
}

static PyObject *
c_get_instance(PyObject *self, PyObject *args)
{
	struct pack *p;
	const char *inst_key = NULL, *inst_value = NULL;
	char *app;
	char *t;
	size_t ts;
	PyObject *dict;

	dict = PyDict_New();

	if (!PyArg_ParseTuple(args, "|ss", &inst_key, &inst_value))
		return NULL;

	if (inst_key && !inst_value)
		return NULL;

	// FIXME: no global instances for now, handle nicely in model.xml
	//if (model_package_profile(bk_node))
		app = bk_app;
	//else
	//	app = NULL;

	p = db_get_profile(bk_node, app, inst_key, inst_value);
	if (!p) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	while (pack_get(p, &t, &ts)) {
		PyObject *val;
		char *t2;
		pack_get(p, &t2, &ts);
		val = PyString_FromStringAndSize(t2, ts);
		PyDict_SetItemString(dict, t, val);
	}

	return dict;
}

static PyMethodDef methods[] = {
	{ "fail", c_fail, METH_VARARGS, "Abort script and return a fail message" },
	{ "notify", c_notify, METH_VARARGS, "Send a notification event" },
	{ "instances", c_instances, METH_VARARGS, "Get list of class's instances from profile" },
	{ "get_profile", c_get_profile, METH_VARARGS, "Get method's arguments from profile" },
	{ "get_instance", c_get_instance, METH_VARARGS, "Get instance's arguments from profile" },
	{ NULL, NULL, 0, NULL }
};

void
csl_setup(void)
{
	Py_Initialize();
}

static void
log_exception(void)
{
	PyObject *pType;
	PyObject *pValue;
	PyObject *pTrace;
	PyObject *eStr;
	PyObject *vStr;

	PyErr_Fetch(&pType, &pValue, &pTrace);
	if (!pType) {
		log_error("csl.c log_exception() called when there isn't an exception\n");
		return;
	}

	eStr = PyObject_Str(pType);
	vStr = PyObject_Str(pValue);
	// FIXME: log traceback too

	log_error("Python Exception [%s]: %s\n",
		PyString_AsString(eStr), PyString_AsString(vStr)
	);
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
		log_exception();
		return CSL_BADCODE;
	}
	pCode = (PyObject *) PyNode_Compile(n, name);
	PyNode_Free(n);
	if (!pCode) {
		log_exception();
		return CSL_BADCODE;
	}

	// serialize code object
#if PY_MINOR_VERSION == 3
	pStr = PyMarshal_WriteObjectToString(pCode);
#else
	pStr = PyMarshal_WriteObjectToString(pCode, 0);
#endif
	Py_DECREF(pCode);
	if (!pStr) {
		return CSL_NOMEM;
	}
	size = PyString_Size(pStr);
	*codeptr = malloc(size);
	if (!*codeptr) {
		Py_DECREF(pStr);
		return CSL_NOMEM;
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
		log_exception();
		return CSL_BADCODE;
	}
	pModule = PyImport_ExecCodeModule("comar", pCode);
	Py_DECREF(pCode);

	if (!pModule || !PyModule_Check(pModule)) {
		puts("no module");
		return CSL_BADCODE;
	}

	pDict = PyModule_GetDict(pModule);
	if (!pDict) {
		puts("no dict");
		Py_DECREF(pModule);
		return CSL_BADCODE;
	}

	pFunc = PyDict_GetItemString(pDict, func_name);
	if (!pFunc || !PyCallable_Check(pFunc)) {
		Py_DECREF(pModule);
		return CSL_NOFUNC;
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

	Py_InitModule("comar", methods);

	pValue = PyObject_Call(pFunc, pArgs, pkArgs);
	if (!pValue) {
		log_exception();
		Py_DECREF(pModule);
		return CSL_FUNCERR;
	}

	pStr = PyObject_Str(pValue);

	Py_DECREF(pValue);
	Py_DECREF(pModule);

	*reslen = PyString_Size(pStr);
	*resptr = malloc((*reslen) + 1);
	if (!*resptr) {
		Py_DECREF(pStr);
		return CSL_NOMEM;
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
