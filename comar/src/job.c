/*
** Copyright (c) 2005-2006, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "csl.h"
#include "process.h"
#include "data.h"
#include "model.h"
#include "log.h"
#include "utility.h"

struct ipc_source bk_channel;
int bk_node;
char *bk_app;

static int
send_result(int cmd, const char *data, size_t size)
{
	struct ipc_struct ipc;
	struct pack *p;

	memset(&ipc, 0, sizeof(struct ipc_struct));
	ipc.source = bk_channel;
	p = pack_new(128);

	if (CMD_RESULT == cmd) {
		if (bk_app)
			pack_put(p, bk_app, strlen(bk_app));
		else
			pack_put(p, "comar", 5);
	}
	if (data) {
		if (size == 0) size = strlen(data);
		pack_put(p, data, size);
	}
	proc_put(TO_PARENT, cmd, &ipc, p);
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
do_event(const char *event, int node, const char *app, struct pack *p)
{
	struct timeval start, end;
	unsigned long msec;
	int e;
	char *code;
	size_t code_size;

	log_debug(LOG_JOB, "Event(%s,%s,%s)\n", event, model_get_path(node), app);

	bk_app = strdup(app);
	bk_node = node;

	csl_setup();

	if (0 != db_get_code(node, app, &code, &code_size)) {
		return -1;
	}

	gettimeofday(&start, NULL);
	e = csl_execute(code, code_size, event, p, NULL, NULL);
	gettimeofday(&end, NULL);

	msec = time_diff(&start, &end);
	if (msec > 60*1000) {
		log_info("Script %s (%s) took %d seconds for %s event.\n", bk_app, model_get_path(node), msec / 1000, event);
	} else {
		log_debug(LOG_PERF, "Script %s (%s) took %d seconds for %s event.\n", bk_app, model_get_path(node), msec / 1000, event);
	}

	return e;
}

static int
do_execute(int node, const char *app, struct pack *pak)
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
		p = pack_dup(pak);
	}

	csl_setup();

	if (0 != db_get_code(model_parent(node), app, &code, &code_size)) {
		send_result(CMD_NONE, "noapp", 5);
		return -1;
	}

	gettimeofday(&start, NULL);
	e = csl_execute(code, code_size, model_get_method(node), pak, &res, &res_size);
	gettimeofday(&end, NULL);
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
		log_info("Script %s took %d seconds for %s call.\n", bk_app, msec / 1000, model_get_path(node));
	} else {
		log_debug(LOG_PERF, "Script %s took %d miliseconds for %s call.\n", bk_app, msec, model_get_path(node));
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

static struct pack *bk_pak;

static void
exec_proc(void)
{
	do_execute(bk_node, bk_app, bk_pak);
}

static int
do_call(int node, struct pack *pak)
{
	struct pack *p = NULL;
	char *apps;
	int ok = 0;

	log_debug(LOG_JOB, "Call(%s)\n", model_get_path(node));

	if (model_flags(node) & P_GLOBAL) {
		p = pack_dup(pak);
	}

	if (db_get_apps(model_parent(node), &apps) != 0) {
		send_result(CMD_NONE, "noapp", 5);
		// FIXME: ok diyecek betik yoksa profile kayıt etmeli mi acaba
		exit(1);
	}

	if (strchr(apps, '/') == NULL) {
		// there is only one script
		if (0 == do_execute(node, apps, pak))
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
			bk_pak = pak;
			p = proc_fork(exec_proc, "ComarSubJob");
			if (p) {
				++cnt;
			} else {
				send_result(CMD_ERROR, "fork failed", 11);
			}
		}
		while(1) {
			struct ipc_struct ipc;
			struct pack *pak;
			pak = pack_new(128);
			proc_listen(&p, &cmd, &size, -1);
			if (cmd == CMD_FINISH) {
				--cnt;
				if (!cnt) break;
			} else {
				if (cmd == CMD_RESULT) ok++;
				proc_get(p, &ipc, pak, size);
				proc_put(TO_PARENT, cmd, &ipc, pak);
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
do_call_package(int node, const char *app, struct pack *p)
{
	log_debug(LOG_JOB, "CallPackage(%s,%s)\n", model_get_path(node), app);

	do_execute(node, app, p);

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
	char *dump;

	log_debug(LOG_JOB, "DumpProfile()\n");

	dump = db_dump_profile();
	if (dump) {
		send_result(CMD_RESULT, dump, strlen(dump));
		free(dump);
	}

	return 0;
}

static void
job_proc(void)
{
	struct ipc_struct ipc;
	struct pack *p;
	struct ProcChild *sender;
	char *t, *s;
	int cmd;
	size_t size;

	p = pack_new(256);
	while (1) {
		if (1 == proc_listen(&sender, &cmd, &size, 1)) break;
	}
	proc_get(sender, &ipc, p, size);

	bk_channel = ipc.source;

	switch (cmd) {
		case CMD_REGISTER:
			pack_get(p, &t, NULL);
			pack_get(p, &s, NULL);
			do_register(ipc.node, t, s);
			break;
		case CMD_REMOVE:
			pack_get(p, &t, NULL);
			do_remove(t);
			break;
		case CMD_CALL:
			do_call(ipc.node, p);
			break;
		case CMD_CALL_PACKAGE:
			pack_get(p, &t, NULL);
			do_call_package(ipc.node, t, p);
			break;
		case CMD_GETLIST:
			do_getlist(ipc.node);
			break;
		case CMD_DUMP_PROFILE:
			do_dump_profile();
			break;
		case CMD_EVENT:
			pack_get(p, &t, NULL);
			pack_get(p, &s, NULL);
			do_event(t, ipc.node, s, p);
			break;
	}
}

int
job_start(int cmd, struct ipc_struct *ipc, struct pack *pak)
{
	struct ProcChild *p;

	p = proc_fork(job_proc, "ComarJob");
	if (!p) return -1;

	if (proc_put(p, cmd, ipc, pak)) return -1;
	return 0;
}
