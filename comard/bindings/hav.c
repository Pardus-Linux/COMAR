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

#include "libcomar.h"

/* wait for comar reply */
int opt_wait = 0;

static struct option longopts[] = {
	{ "help", 0, 0, 'h' },
	{ "version", 0, 0, 'v' },
	{ "wait", 0, 0, 'w' },
	{ 0, 0, 0, 0 }
};
static char *shortopts = "hvw";

static void
print_usage(void)
{
	puts(
		"Command line COMAR interface."
		"usage: hav [options] <command> [args]\n"
		"commands:\n"
		"   call <method-name> [parameter=value]...\n"
		"   register <class> <package-name> <script-file>\n"
		"   remove <package-name>\n"
		"   list <class>\n"
		"options:\n"
		"   -w, --wait\n"
		"report bugs to <gurer@uludag.org.tr>"
	);
}

static void
do_call(char *argv[])
{
	for(; argv[optind]; optind++)
		printf("args[%s]\n",argv[optind]);
}

static void
do_register(char *argv[])
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

	if (!argv[optind] || !argv[optind+1] || !argv[optind+2]) {
		print_usage();
		exit(1);
	}

	comar_send(
		com, 1,
		COMAR_REGISTER,
		argv[optind], argv[optind+1], argv[optind+2],
		NULL
	);

	if (opt_wait) {
		while(comar_read(com, &cmd, &id, &ret, -1)) {
			printf("cmd=%d, id=%d, arg=[%s]\n", cmd, id, ret);
		}
	}

	comar_disconnect(com);
}

static void
do_remove(char *argv[])
{
	comar_t *com;

	com = comar_connect();
	if (!com) {
		puts("Cannot connect to COMAR daemon");
		exit(2);
	}

	if (!argv[optind]) {
		print_usage();
		exit(1);
	}

	comar_send(
		com, 1,
		COMAR_REMOVE,
		argv[optind],
		NULL
	);

	if (opt_wait) {
		sleep(5);
	}

	comar_disconnect(com);
}

static void
do_list(char *argv[])
{
}

static struct cmd_s {
	const char *cmd;
	void (*func)(char *argv[]);
} commands[] = {
	{ "call", do_call },
	{ "register", do_register },
	{ "remove", do_remove },
	{ "list", do_list },
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
				opt_wait = 1;
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
