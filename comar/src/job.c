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
#include "log.h"
#include "ipc.h"
#include "utility.h"

static unsigned char *
load_file(const char *fname, int *sizeptr)
{
	FILE *f;
	struct stat fs;
	size_t size;
	unsigned char *data;

	if (stat(fname, &fs) != 0) return NULL;
	size = fs.st_size;
	if (sizeptr) *sizeptr = size;

	data = malloc(size + 1);
	if (!data) return NULL;
	memset(data, 0, size + 1);

	f = fopen(fname, "rb");
	if (!f) {
		free(data);
		return NULL;
	}
	if (fread(data, size, 1, f) < 1) {
		free(data);
		return NULL;
	}
	fclose(f);

	return data;
}

static void *chan;
static int chan_id;
int bk_node;
char *bk_app;

static int
send_result(int cmd, const char *data, size_t size)
{
	ipc_start(cmd, chan, chan_id, 0);
	if (CMD_RESULT == cmd) {
		if (bk_app)
			ipc_pack_arg(bk_app, strlen(bk_app));
		else
			ipc_pack_arg("comar", 5);
	}
	if (data) {
		if (size == 0) size = strlen(data);
		ipc_pack_arg(data, size);
	}
	ipc_send(TO_PARENT);
	return 0;
}

// FIXME: refactor
int
job_send_result(int cmd, const char *data, size_t size)
{
	return send_result(cmd, data, size);
}

static int
do_register(int node, const char *app, const char *fname)
{
	char *buf;
	char *code;
	size_t codelen;
	int e;

	log_debug(LOG_JOB, "Register(%s,%s,%s)\n", model_get_path(node), app, fname);

	csl_setup();

	buf = load_file(fname, NULL);
	if (!buf) {
		send_result(CMD_ERROR, "no file", 7);
		return -1;
	}

	e = csl_compile(buf, "test", &code, &codelen);
	if (e) {
		send_result(CMD_ERROR, "compile error", 13);
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
	log_debug(LOG_JOB, "Remove(%s)\n", app);

	db_del_app(app);

	send_result(CMD_RESULT, "removed", 7);

	return 0;
}

static int
do_execute(int node, const char *app)
{
	struct timeval start, end;
	unsigned long msec;
	struct pack *p = NULL;
	char *code;
	char *res;
	size_t code_size;
	size_t res_size;
	int e;

	log_debug(LOG_JOB, "Execute(%s,%s)\n", model_get_path(node), app);

	bk_app = strdup(app);
	bk_node = node;

	if (model_flags(node) & P_PACKAGE) {
		p = ipc_into_pack();
	}

	csl_setup();

	if (0 != db_get_code(model_parent(node), app, &code, &code_size)) {
		send_result(CMD_NONE, "noapp", 5);
		return -1;
	}

	gettimeofday (&start, NULL);
	e = csl_execute(code, code_size, model_get_method(node), &res, &res_size);
	gettimeofday (&end, NULL);
	if (e) {
		if (e == CSL_NOFUNC)
			send_result(CMD_NONE, "nomethod", 8);
		else
			send_result(CMD_ERROR, "err", 3);
	} else {
		send_result(CMD_RESULT, res, res_size);
		free(res);
	}

	msec = time_diff(&start, &end);
	if (msec > 60*1000) {
		log_info("Script %s took %d seconds for %s call.\n", app, msec / 1000, model_get_path(node));
	} else {
		log_debug(LOG_PERF, "Script %s took %d miliseconds for %s call.\n", app, msec, model_get_path(node));
	}

	if (model_flags(node) & P_PACKAGE) {
		if (0 == e) {
			if (model_flags(node) & P_DELETE)
				db_del_profile(node, bk_app, p);
			else
				db_put_profile(node, bk_app, p);
		}
		pack_delete(p);
	}

	csl_cleanup();

	return e;
}

static void
exec_proc(void)
{
	do_execute(bk_node, bk_app);
}

static int
do_call(int node)
{
	struct pack *p = NULL;
	char *apps;
	int ok = 0;

	log_debug(LOG_JOB, "Call(%s)\n", model_get_path(node));

	if (model_flags(node) & P_GLOBAL) {
		p = ipc_into_pack();
	}

	if (db_get_apps(model_parent(node), &apps) != 0) {
		send_result(CMD_NONE, "noapp", 5);
		// FIXME: ok diyecek betik yoksa profile kayıt etmeli mi acaba
		exit(1);
	}

	if (strchr(apps, '/') == NULL) {
		// there is only one script
		if (0 == do_execute(node, apps))
			ok = 1;
	} else {
		// multiple scripts, run concurrently
		char *t, *s;
		struct ProcChild *p;
		int cmd;
		int cnt = 0;
		size_t size;

		// FIXME: package count
		send_result(CMD_RESULT_START, NULL, 0);
		for (t = apps; t; t = s) {
			s = strchr(t, '/');
			if (s) {
				*s = '\0';
				++s;
			}
			bk_node = node;
			bk_app = t;
			p = proc_fork(exec_proc, "SubJob");
			if (p) {
				++cnt;
			} else {
				send_result(CMD_ERROR, "fork failed", 11);
			}
		}
		while(1) {
			struct ipc_data *ipc;
			proc_listen(&p, &cmd, &size, -1);
			if (cmd == CMD_FINISH) {
				--cnt;
				if (!cnt) break;
			} else {
				if (cmd == CMD_RESULT) ok++;
				proc_recv(p, &ipc, size);
				proc_send(TO_PARENT, cmd, ipc, size);
			}
		}
		send_result(CMD_RESULT_END, NULL, 0);
	}

    if ((model_flags(node) & P_GLOBAL) && ok) {
		db_put_profile(node, NULL, p);
		pack_delete(p);
	}

	return 0;
}

static int
do_call_package(int node, const char *app)
{
	log_debug(LOG_JOB, "CallPackage(%s,%s)\n", model_get_path(node), app);

	do_execute(node, app);

	return 0;
}

static int
do_getlist(int node)
{
	char *apps;

	log_debug(LOG_JOB, "GetList(%s)\n", model_get_path(node));

	if (db_get_apps(node, &apps) != 0) {
		send_result(CMD_RESULT, NULL, 0);
	} else {
		char *t;
		for (t = apps; *t; t++) {
			if (*t == '/') *t = '\n';
		}
		send_result(CMD_RESULT, apps, 0);
	}
	return 0;
}

static int
do_dump_profile(void)
{
	log_debug(LOG_JOB, "DumpProfile()\n");

	db_dump_profile();
	// FIXME: send dump to the requester
	send_result(CMD_RESULT, NULL, 0);

	return 0;
}

static void
job_proc(void)
{
	struct ProcChild *sender;
	char *t, *s;
	int cmd;
	size_t size;

	while (1) {
		if (1 == proc_listen(&sender, &cmd, &size, 1)) break;
	}
	ipc_recv(sender, size);

	chan = ipc_get_data();
	chan_id = ipc_get_id();

	switch (cmd) {
		case CMD_REGISTER:
			ipc_get_arg(&t, NULL);
			ipc_get_arg(&s, NULL);
			do_register(ipc_get_node(), t, s);
			break;
		case CMD_REMOVE:
			ipc_get_arg(&t, NULL);
			do_remove(t);
			break;
		case CMD_CALL:
			do_call(ipc_get_node());
			break;
		case CMD_CALL_PACKAGE:
			ipc_get_arg(&t, NULL);
			do_call_package(ipc_get_node(), t);
			break;
		case CMD_GETLIST:
			do_getlist(ipc_get_node());
			break;
		case CMD_DUMP_PROFILE:
			do_dump_profile();
			break;
	}
}

int
job_start(int cmd, char *ipc_msg, size_t ipc_size)
{
	struct ProcChild *p;

	p = proc_fork(job_proc, "Job");
	if (!p) return -1;
	if (proc_send(p, cmd, ipc_msg, ipc_size)) return -1;
	return 0;
}
