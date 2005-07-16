/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#include "csl.h"
#include "process.h"
#include "data.h"
#include "model.h"
#include "rpc.h"

static unsigned char *
load_file(const char *fname, int *sizeptr)
{
	FILE *f;
	struct stat fs;
	size_t size;
	unsigned char *data;

	if (stat (fname, &fs) != 0) {
		printf ("Cannot stat file '%s'\n", fname);
		return NULL;
	}
	size = fs.st_size;
	if (sizeptr) *sizeptr = size;

	data = malloc (size + 1);
	if (!data) {
		printf ("Cannot allocate %d bytes\n", size);
		return NULL;
	}
	memset(data, 0, size + 1);

	f = fopen (fname, "rb");
	if (!f) {
		printf ("Cannot open file '%s'\n", fname);
		return NULL;
	}

	if (fread (data, size, 1, f) < 1) {
		printf ("Read error in file '%s'\n", fname);
		return NULL;
	}

	fclose (f);
	return data;
}

static void *chan;

static int
send_result(int cmd, const char *data, size_t size)
{
	struct ipc_data *ipc;

	if (size == 0) size = strlen(data);
	ipc = malloc(sizeof(struct ipc_data) + size);
	ipc->chan = chan;
	ipc->app_len = size;
	memcpy(&ipc->data[0], data, size);
	proc_send(TO_PARENT, cmd, ipc, sizeof(struct ipc_data) + size);
	free(ipc);
	return 0;
}

static int
do_register(int node, const char *app, const char *fname)
{
	char *buf;
	char *code;
	size_t codelen;
	int e;
printf("Register(%s,%s,%s)\n", model_get_path(node), app, fname);
	csl_setup();

	buf = load_file(fname, NULL);
	if (!buf) {
		send_result(CMD_FAIL, "no file", 7);
		return -1;
	}

	e = csl_compile(buf, "test", &code, &codelen);
	if (e) {
		send_result(CMD_FAIL, "compile error", 13);
		return -1;
	}

	db_put_script(node, app, code, codelen);

	send_result(CMD_RESULT, "registered", 10);

	csl_cleanup();

	return 0;
}

static int
do_remove(const char *app)
{
printf("Remove(%s)\n", app);
	db_del_app(app);
	return 0;
}

static int
do_execute(int node, const char *app)
{
	char *code;
	char *res;
	size_t code_size;
	size_t res_size;
	int e;
printf("Execute(%s,%s)\n", model_get_path(node), app);
	csl_setup();

	if (0 != db_get_code(model_parent(node), app, &code, &code_size)) return -1;
	e = csl_execute(code, code_size, model_get_method(node), &res, &res_size);
	if (e) {
		send_result(CMD_FAIL, "err", 3);
	} else {
		send_result(CMD_RESULT, res, res_size);
	}
	free(res);

	csl_cleanup();

	return e;
}

int bk_node;
char *bk_app;

static void
exec_proc(void)
{
	do_execute(bk_node, bk_app);
}

static int
do_call(int node)		// FIXME: app, args
{
	char *apps;
printf("Call(%s)\n", model_get_path(node));

	if (db_get_apps(model_parent(node), &apps) != 0) {
		send_result(CMD_RESULT, "no app", 6);
		exit(1);
	}

	if (strchr(apps, '/') == NULL) {
		do_execute(node, apps);
	} else {
		char *t, *s;
		struct ProcChild *p;
		int cmd;
		int cnt = 0;
		size_t size;

		for (t = apps; t; t = s) {
			s = strchr(t, '/');
			if (s) {
				*s = '\0';
				++s;
			}
			bk_node = node;
			bk_app = t;
			p = proc_fork(exec_proc);
			if (p) ++cnt;
		}
		while(cnt && proc_listen(&p, &cmd, &size, 1) == 1) {
			struct ipc_data *ipc;
			if (cmd == CMD_RESULT || cmd == CMD_FAIL) {
				proc_recv(p, &ipc, size);
				proc_send(TO_PARENT, cmd, ipc, size);
				--cnt;
			}
		}
	}

	free(apps);

	return 0;
}

static void
job_proc(void)
{
	struct ProcChild *sender;
	struct ipc_data *ipc;
	int cmd;
	size_t size;

	while (1) {
		if (1 == proc_listen(&sender, &cmd, &size, 1)) break;
	}
	proc_recv(sender, &ipc, size);

	chan = ipc->chan;
	switch (cmd) {
		case CMD_REGISTER:
			do_register(ipc->node, &ipc->data[0], &ipc->data[0] + ipc->app_len + 1);
			break;
		case CMD_REMOVE:
			do_remove(&ipc->data[0]);
			break;
		case CMD_CALL:
			do_call(ipc->node);
			break;
	}
}

int
job_start(int cmd, struct ipc_data *ipc_msg, size_t ipc_size)
{
	struct ProcChild *p;

	p = proc_fork(job_proc);
	if (!p) return -1;
	if (proc_send(p, cmd, ipc_msg, ipc_size)) return -1;
	return 0;
}
