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
		exit (2);
	}
	size = fs.st_size;
	if (sizeptr) *sizeptr = size;

	data = malloc (size + 1);
	if (!data) {
		printf ("Cannot allocate %d bytes\n", size);
		exit (2);
	}
	memset(data, 0, size + 1);

	f = fopen (fname, "rb");
	if (!f) {
		printf ("Cannot open file '%s'\n", fname);
		exit (2);
	}

	if (fread (data, size, 1, f) < 1) {
		printf ("Read error in file '%s'\n", fname);
		exit (2);
	}

	fclose (f);
	return data;
}

static void
register_proc(void)
{
	struct reg_cmd *cmd;
	struct ProcChild *sender;
	char *buf;
	char *code;
	size_t codelen;
	int e;
	int c;
	size_t size;

	while (1) {
		if (1 == proc_listen(&sender, &c, &size, 1)) break;
	}
	proc_recv(sender, &cmd, size);

	csl_setup();

	buf = load_file(&cmd->data[0] + cmd->app_len + 1, NULL);
	if (!buf) {
		proc_send(TO_PARENT, CMD_FAIL, NULL, 0);
		exit(1);
	}

	e = csl_compile(buf, "test", &code, &codelen);
	if (e) {
		proc_send(TO_PARENT, CMD_FAIL, NULL, 0);
		exit(1);
	}

	db_put_script(cmd->node, &cmd->data[0], code, codelen);

	proc_send(TO_PARENT, CMD_RESULT, NULL, 0);

	csl_cleanup();
}

int
job_start_register(int node_no, const char *app, const char *csl_file)
{
	struct ProcChild *p;
	struct reg_cmd *cmd;
	size_t sz;

	sz = sizeof(struct reg_cmd) + strlen(app) + strlen(csl_file);
	cmd = malloc(sz);
	if (!cmd) return -1;
	cmd->node = node_no;
	cmd->app_len = strlen(app);
	strcpy(&cmd->data[0], app);
	strcpy(&cmd->data[0] + strlen(app) + 1, csl_file);
	p = proc_fork(register_proc);
	if (!p) {
		free(cmd);
		return -1;
	}
	proc_send(p, CMD_CALL, cmd, sz);
	free(cmd);
	return 0;
}

static void
exec_proc(void)
{
	struct ProcChild *sender;
	struct call_cmd *cmd;
	char *apps;
	char *code;
	char *res;
	size_t reslen;
	size_t size;
	int c;
	int e;

	while (1) {
		if (1 == proc_listen(&sender, &c, &size, 1)) break;
	}
	proc_recv(sender, &cmd, size);

	csl_setup();

	if (db_open_node(model_parent(cmd->node), &apps) != 0) {
		proc_send(TO_PARENT, CMD_FAIL, NULL, 0);
		exit(1);
	}

	// FIXME: multiple apps & value return
	db_get_code(apps, &code, &size);
	e = csl_execute(code, size, model_get_method(cmd->node), &res, &reslen);
	free(res);

	db_close_node();

	csl_cleanup();
}

int
job_start_execute(int node_no, const char *app) // FIXME: args
{
	struct ProcChild *p;
	struct call_cmd cmd;

	cmd.node = node_no;

	p = proc_fork(exec_proc);
	if (!p) return -1;
	proc_send(p, CMD_CALL, &cmd, sizeof(struct call_cmd));
	return 0;
}
