/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stddef.h>
#include <stdarg.h>
#include <getopt.h>
#include <sys/stat.h>

#include "comar.h"

/* wait for comar reply */
int opt_wait = 1;

static struct option longopts[] = {
	{ "help", 0, 0, 'h' },
	{ "version", 0, 0, 'v' },
	{ "nowait", 0, 0, 'w' },
	{ 0, 0, 0, 0 }
};
static char *shortopts = "hvw";

static void
print_usage(void)
{
	puts(
		"Command line COMAR interface.\n"
		"usage: hav [options] <command> [args]\n"
		"commands:\n"
		"   call <method-name> [parameter value]...\n"
		"   call-package <method-name> <package-name> [parameter value]...\n"
		"   register <class> <package-name> <script-file>\n"
		"   remove <package-name>\n"
		"   list <class>\n"
		"   listen <notify-name>...\n"
		"   event <class-name> <func-name> <package-name> <data>\n"
		"   dump\n"
		"options:\n"
		"   -w, --nowait        Do not wait for an answer.\n"
		"report bugs to <gurer@uludag.org.tr>"
	);
}

static void
do_call(char *argv[])
{
	comar_t *com;
	int cmd;
	unsigned int id;
	char *ret;

	com = comar_connect();
	if (!com) {
		puts("Cannot connect to COMAR daemon");
		exit(2);
	}

	comar_send_start(com, 1, COMAR_CALL);

	for(; argv[optind]; optind++) {
		comar_send_arg(com, argv[optind], 0);
	}

	comar_send_finish(com);

	if (opt_wait) {
		comar_wait(com, -1);
		if (!comar_read(com, &cmd, &id, &ret)) {
			puts("Connection closed by COMAR daemon");
			exit(2);
		}
		printf("%s id=%d, arg=[%s]\n", comar_cmd_name(cmd), id, ret);
		if (cmd == COMAR_RESULT_START) {
			while (cmd != COMAR_RESULT_END) {
				comar_wait(com, -1);
				if (!comar_read(com, &cmd, &id, &ret)) {
					puts("Connection closed by COMAR daemon");
					exit(2);
				}
				if (cmd == COMAR_RESULT)
					printf("%s id=%d, pak=[%s], arg=[%s]\n", comar_cmd_name(cmd), id, comar_package_name(com), ret);
				else
					printf("%s id=%d, arg=[%s]\n", comar_cmd_name(cmd), id, ret);
			}
		}
	}

	comar_disconnect(com);
}

static void
do_call_package(char *argv[])
{
	comar_t *com;
	int cmd;
	unsigned int id;
	char *ret;

	com = comar_connect();
	if (!com) {
		puts("Cannot connect to COMAR daemon");
		exit(2);
	}

	comar_send_start(com, 1, COMAR_CALL_PACKAGE);

	for(; argv[optind]; optind++) {
		comar_send_arg(com, argv[optind], 0);
	}

	comar_send_finish(com);

	if (opt_wait) {
		comar_wait(com, -1);
		if (!comar_read(com, &cmd, &id, &ret)) {
			puts("Connection closed by COMAR daemon");
			exit(2);
		}
		printf("%s id=%d, arg=[%s]\n", comar_cmd_name(cmd), id, ret);
	}

	comar_disconnect(com);
}

static void
do_register(char *argv[])
{
	comar_t *com;
	int cmd;
	unsigned int id;
	char *ret;
	char *path;

	if (!argv[optind] || !argv[optind+1] || !argv[optind+2]) {
		print_usage();
		exit(1);
	}

	path = argv[optind + 2];
	if (path[0] != '/') {
		path = realpath(path, NULL);
	}

	com = comar_connect();
	if (!com) {
		puts("Cannot connect to COMAR daemon");
		exit(2);
	}

	comar_send(
		com, 1,
		COMAR_REGISTER,
		argv[optind], argv[optind+1], path,
		NULL
	);

	if (opt_wait) {
		comar_wait(com, -1);
		if (!comar_read(com, &cmd, &id, &ret)) {
			puts("Connection closed by COMAR daemon");
			exit(2);
		}
		printf("%s id=%d, arg=[%s]\n", comar_cmd_name(cmd), id, ret);
	}

	comar_disconnect(com);
}

static void
do_remove(char *argv[])
{
	comar_t *com;
	int cmd;
	unsigned int id;
	char *ret;

	if (!argv[optind]) {
		print_usage();
		exit(1);
	}

	com = comar_connect();
	if (!com) {
		puts("Cannot connect to COMAR daemon");
		exit(2);
	}

	comar_send(
		com, 1,
		COMAR_REMOVE,
		argv[optind],
		NULL
	);

	if (opt_wait) {
		comar_wait(com, -1);
		if (!comar_read(com, &cmd, &id, &ret)) {
			puts("Connection closed by COMAR daemon");
			exit(2);
		}
		printf("%s id=%d, arg=[%s]\n", comar_cmd_name(cmd), id, ret);
	}

	comar_disconnect(com);
}

static void
do_list(char *argv[])
{
	comar_t *com;
	int cmd;
	unsigned int id;
	char *ret;

	if (!argv[optind]) {
		print_usage();
		exit(1);
	}

	com = comar_connect();
	if (!com) {
		puts("Cannot connect to COMAR daemon");
		exit(2);
	}

	comar_send(
		com, 1,
		COMAR_GETLIST,
		argv[optind],
		NULL
	);

	comar_wait(com, -1);
	if (!comar_read(com, &cmd, &id, &ret)) {
		puts("Connection closed by COMAR daemon");
		exit(2);
	}
	printf("%s id=%d, arg=[%s]\n", comar_cmd_name(cmd), id, ret);

	comar_disconnect(com);
}

static void
do_listen(char *argv[])
{
	comar_t *com;
	int cmd;
	unsigned int id;
	char *ret;

	com = comar_connect();
	if (!com) {
		puts("Cannot connect to COMAR daemon");
		exit(2);
	}

	while (argv[optind]) {
		comar_send(com, 1, COMAR_ASKNOTIFY, argv[optind], NULL);
		++optind;
	}

	while (1) {
		comar_wait(com, -1);
		if (!comar_read(com, &cmd, &id, &ret)) {
			puts("Connection closed by COMAR daemon");
			exit(2);
		}
		printf("%s id=%d, arg=[%s]\n", comar_cmd_name(cmd), id, ret);
	}

	comar_disconnect(com);
}

static void
do_dump(char *argv[])
{
	comar_t *com;
	int cmd;
	unsigned int id;
	char *ret;

	com = comar_connect();
	if (!com) {
		puts("Cannot connect to COMAR daemon");
		exit(2);
	}

	comar_send(
		com, 1,
		COMAR_DUMP_PROFILE,
		NULL
	);

	comar_wait(com, -1);
	if (!comar_read(com, &cmd, &id, &ret)) {
		puts("Connection closed by COMAR daemon");
		exit(2);
	}
	printf("%s id=%d, arg=[%s]\n", comar_cmd_name(cmd), id, ret);

	comar_disconnect(com);
}

static void
do_event(char *argv[])
{
	comar_t *com;

	if (!argv[optind] || !argv[optind+1] || !argv[optind+2] || !argv[optind+3]) {
		print_usage();
		exit(1);
	}

	com = comar_connect();
	if (!com) {
		puts("Cannot connect to COMAR daemon");
		exit(2);
	}

	comar_send(
		com, 1,
		COMAR_EVENT,
		argv[optind],
		argv[optind+1],
		argv[optind+2],
		argv[optind+3],
		NULL
	);

	comar_disconnect(com);
}

static struct cmd_s {
	const char *cmd;
	void (*func)(char *argv[]);
} commands[] = {
	{ "call", do_call },
	{ "call-package", do_call_package },
	{ "register", do_register },
	{ "remove", do_remove },
	{ "list", do_list },
	{ "listen", do_listen },
	{ "dump", do_dump },
	{ "event", do_event },
};

int
main(int argc, char *argv[])
{
	int c, i;
	char *cmd;

	while ((c = getopt_long(argc, argv, shortopts, longopts, &i)) != -1) {
		switch (c) {
			case 'h':
				print_usage();
				exit(0);
			case 'v':
				puts("hav 1.0");
				exit(0);
			case 'w':
				opt_wait = 0;
				break;
		}
	}
	if (optind >= argc) {
		print_usage();
		exit(1);
	}

	cmd = argv[optind++];
	for (i = 0; i < sizeof(commands) / sizeof(struct cmd_s); i++) {
		if (strcmp(commands[i].cmd, cmd) == 0) {
			commands[i].func(argv);
			return 0;
		}
	}
	printf("Unknown command '%s'\n", cmd);
	return 1;
}
