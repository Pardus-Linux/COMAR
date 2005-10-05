/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <Python.h>
#include <sys/time.h>

static PyObject *
csapi_atoi(PyObject *self, PyObject *args)
{
	char *str;
	int i;

	if (!PyArg_ParseTuple(args, "s", &str))
		return NULL;

	i = atoi(str);
	return Py_BuildValue("i", i);
}

static PyObject *
csapi_settimeofday(PyObject *self, PyObject *args)
{
	struct timeval tv;
	double t;

	if (!PyArg_ParseTuple(args, "d", &t))
		return NULL;

	tv.tv_sec = t;
	tv.tv_usec = 0;
	if (0 != settimeofday(&tv, NULL))
		return NULL;

	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef methods[] = {
	{ "atoi", csapi_atoi, METH_VARARGS,
		"Convert a string into an integer." },
	{ "settimeofday", csapi_settimeofday, METH_VARARGS,
		"Set system date." },
	{ NULL, NULL, 0, NULL }
};

PyMODINIT_FUNC
initcsapi(void)
{
	Py_InitModule("csapi", methods);
}
