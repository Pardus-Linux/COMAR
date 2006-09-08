/*
** Copyright (c) 2005-2006, TUBITAK/UEKAE
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
#include "notify.h"
#include "log.h"
#include "model.h"
#include "data.h"
#include "utility.h"
#include "job.h"

// FIXME: cleanup
int job_send_result(int cmd, const char *data, size_t size);
extern int bk_node;
extern char *bk_app;
extern struct ipc_source bk_channel;

static PyObject *
c_script(PyObject *self, PyObject *args)
{
	PyObject *tuple;

	tuple = PyTuple_Pack(1, PyString_FromString(bk_app));
	return tuple;
}

static PyObject *
c_i18n(PyObject *self, PyObject *args)
{
	char lang[4];
	PyObject *dict;
	PyObject *ret;

	lang[0] = bk_channel.lang[0];
	if (lang[0] == '\0') lang[0] = 'e';
	lang[1] = bk_channel.lang[1];
	if (lang[1] == '\0') lang[1] = 'n';
	lang[2] = '\0';

	if (!PyArg_ParseTuple(args, "O!", &PyDict_Type, &dict))
		return NULL;

	ret = PyDict_GetItemString(dict, lang);
	if (ret) Py_INCREF(ret);
	return ret;
}

static PyObject *
c_call(PyObject *self, PyObject *args)
{
	struct ipc_struct ipc;
	struct pack *p;
	char *node;
	char *pak;
	int nd;

	if (!PyArg_ParseTuple(args, "ss", &node, &pak))
		return NULL;

	nd = model_lookup_method(node);
	if (nd == -1) return NULL;

	memset(&ipc, 0, sizeof(struct ipc_struct));
	ipc.node = nd;
	p = pack_new(128);
	pack_put(p, pak, strlen(pak));

	job_start(CMD_CALL_PACKAGE, &ipc, p);

	while (1) {
		struct ProcChild *sender;
		int cmd;
		int size;

		if (1 == proc_listen(&sender, &cmd, &size, 1)) {
			switch (cmd) {
				case CMD_RESULT:
				case CMD_FAIL:
				case CMD_ERROR:
				case CMD_NONE:
					proc_get(sender, &ipc, p, size);
					break;
				case CMD_NOTIFY:
					proc_get(sender, &ipc, p, size);
					proc_put(TO_PARENT, cmd, &ipc, p);
					break;
			}
			if (cmd == CMD_FINISH) break;
		}
	}
	Py_INCREF(Py_None);
	return Py_None;
}

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

	if (!PyArg_ParseTuple(args, "ss", &name, &msg))
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
	if (!p) return;
	PyList_Append(c_instances_list, p);
}

static PyObject *
c_instances(PyObject *self, PyObject *args)
{
	const char *key = NULL;
	char *app;

	proc_check_shutdown();

	c_instances_list = PyList_New(0);
	if (!c_instances_list) return NULL;

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

	proc_check_shutdown();

	dict = PyDict_New();

	if (!PyArg_ParseTuple(args, "|s", &node))
		return NULL;

	if (node)
		node_no = model_lookup_method(node);
	else
		node_no = bk_node;

	if (model_flags(node_no) & P_PACKAGE)
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

	proc_check_shutdown();

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
	{ "script", c_script, METH_NOARGS, "Return package name" },
	{ "_", c_i18n, METH_VARARGS, "Return localized text from a dictionary" },
	{ "call", c_call, METH_VARARGS, "Make a syncronous comar call" },
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
	char *eStr;
	char *vStr = "";
	long lineno = 0;

	PyErr_Fetch(&pType, &pValue, &pTrace);
	if (!pType) {
		log_error("csl.c log_exception() called when there isn't an exception\n");
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

	log_error("Python Exception [%s] in (%s,%s,%ld): %s\n",
		eStr, model_get_path(bk_node), bk_app, lineno, vStr
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
csl_execute(char *code, size_t size, const char *func_name, struct pack *pak, char **resptr, int *reslen)
{
	PyObject *pCode, *pModule, *pDict, *pFunc, *pValue, *pStr;
	PyObject *pArgs, *pkArgs;
	PyMethodDef *meth;
	node *n;

	pModule = PyImport_AddModule("__builtin__");
	pDict = PyModule_GetDict(pModule);
	for (meth = methods; meth->ml_name; meth++) {
		pCode = PyCFunction_New(meth, NULL);
		PyDict_SetItemString(pDict, meth->ml_name, pCode);
	}

	if (size == 0) {
		n = PyParser_SimpleParseString(code, Py_file_input);
		if (!n) {
			log_exception();
			return CSL_BADCODE;
		}
		pCode = (PyObject *) PyNode_Compile(n, "lala");
		PyNode_Free(n);
		if (!pCode) {
			log_exception();
			return CSL_BADCODE;
		}
	} else {
		pCode = PyMarshal_ReadObjectFromString(code, size);
		if (!pCode) {
			log_exception();
			return CSL_BADCODE;
		}
	}
	pModule = PyImport_ExecCodeModule("csl", pCode);
	Py_DECREF(pCode);

	if (!pModule || !PyModule_Check(pModule)) {
		return CSL_BADCODE;
	}

	pDict = PyModule_GetDict(pModule);
	if (!pDict) {
		Py_DECREF(pModule);
		return CSL_BADCODE;
	}

	pFunc = PyDict_GetItemString(pDict, func_name);
	if (!pFunc || !PyCallable_Check(pFunc)) {
		Py_DECREF(pModule);
		return CSL_NOFUNC;
	}

	pArgs = NULL;
	pkArgs = PyDict_New();
	while (pak) {
		PyObject *p;
		char *t, *t2;
		size_t sz;
		if (pack_get(pak, &t, &sz) == 0) break;
		if (pack_get(pak, &t2, &sz) == 0) {
			pArgs = PyTuple_New(1);
			PyTuple_SetItem(pArgs, 0, PyString_FromString(t));
			Py_DECREF(pkArgs);
			break;
		}
		p = PyString_FromStringAndSize(t2, sz);
		PyDict_SetItemString(pkArgs, t, p);
	}
	if (!pArgs) pArgs = PyTuple_New(0);

	pValue = PyObject_Call(pFunc, pArgs, pkArgs);
	if (!pValue) {
		log_exception();
		Py_DECREF(pModule);
		return CSL_FUNCERR;
	}

	pStr = PyObject_Str(pValue);

	Py_DECREF(pValue);
	Py_DECREF(pModule);

	// is return value asked?
	if (resptr == NULL) return 0;

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
