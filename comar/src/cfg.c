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
#include <getopt.h>

#include "i18n.h"
#include "log.h"
#include "cfg.h"
#include "process.h"

/* global option variables with defaults */
char *cfg_model_file = "/etc/comar/model.xml";
char *cfg_data_dir = "/var/db/comar";
char *cfg_socket_name = "/var/run/comar.socket";
int cfg_log_console = 0;
int cfg_log_file = 1;
char *cfg_log_file_name = "/var/log/comar.log";
int cfg_log_flags = 0;
int cfg_stop_only = 0;

static struct logflag_struct {
	const char *flag;
	int value;
} logflags[] = {
	{ "proc", LOG_PROC },
	{ "db", LOG_DB },
	{ "job", LOG_JOB },
	{ "ipc", LOG_IPC },
	{ "perf", LOG_PERF },
	{ "all", LOG_ALL },
	{ "full", LOG_ALL },
	{ NULL, 0 }
};

static struct option longopts[] = {
	{ "model", required_argument, NULL, 'm' },
	{ "datadir", required_argument, NULL, 'd' },
	{ "socket", required_argument, NULL, 's' },
	{ "debug", required_argument, NULL, 'g' },
	{ "stop", 0, NULL, 'q' },
	{ "print", 0, NULL, 'p' },
	{ "help", 0, NULL, 'h' },
	{ "version", 0, NULL, 'v' },
	{ NULL, 0, NULL, 0 }
};

static char *shortopts = "m:d:s:g:phv";

static void
print_usage(void)
{
	puts(
		_("Usage: comar [OPTIONS]\n"
		"Pardus configuration manager.\n"
		" -m, --model [FILE]  Use the given xml model file.\n"
		" -d, --datadir [DIR] Data storage directory.\n"
		" -s, --socket [NAME] RPC unix socket name.\n"
		" -g, --debug [FLAGS] Enable debug output.\n"
		" -p, --print         Print debug messages to console.\n"
		"     --stop          Stop running comar and exit.\n"
		" -h, --help          Print this text and exit.\n"
		" -v, --version       Print version and exit.\n"
		"Report bugs to http://bugs.pardus.org.tr")
	);
}

static void
print_version(void)
{
	printf(
		_("COMAR %s\n"
		"Copyright (c) 2005-2006, TUBITAK/UEKAE\n"
		"This program is free software; you can redistribute it and/or modify it\n"
		"under the terms of the GNU General Public License as published by the\n"
		"Free Software Foundation; either version 2 of the License, or (at your\n"
		"option) any later version.\n"),
		VERSION
	);
}

void
cfg_init(int argc, char *argv[])
{
	int c, i, j;

	while ((c = getopt_long(argc, argv, shortopts, longopts, &i)) != -1) {
		switch (c) {
			case 'm':
				cfg_model_file = strdup(optarg);
				break;
			case 'd':
				cfg_data_dir = strdup(optarg);
				break;
			case 's':
				cfg_socket_name = strdup(optarg);
				break;
			case 'g':
				for (j = 0; logflags[j].flag; ++j) {
					if (strstr(optarg, logflags[j].flag))
						cfg_log_flags |= logflags[j].value;
				}
				break;
			case 'p':
				cfg_log_console = 1;
				break;
			case 'q':
				cfg_stop_only = 1;
				break;
			case 'h':
				print_usage();
				exit(0);
			case 'v':
				print_version();
				exit(0);
			default:
				exit(1);
		}
	}
}
