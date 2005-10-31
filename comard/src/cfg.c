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
#include <getopt.h>

#include "i18n.h"
#include "log.h"
#include "cfg.h"

/* global option variables with defaults */
char *cfg_model_file = "/etc/comar/model.xml";
char *cfg_data_dir = "/var/db/comar";
int cfg_log_console = 0;
int cfg_log_file = 1;
char *cfg_log_file_name = "/var/log/comar.log";
int cfg_log_flags = LOG_JOB;	// FIXME: for alpha releases

static struct logflag_struct {
	const char *flag;
	int value;
} logflags[] = {
	{ "proc", LOG_PROC },
	{ "db", LOG_DB },
	{ "job", LOG_JOB },
	{ "ipc", LOG_IPC },
	{ "all", LOG_ALL },
	{ "full", LOG_ALL },
	{ NULL, 0 }
};

static struct option longopts[] = {
	{ "model", required_argument, NULL, 'm' },
	{ "datadir", required_argument, NULL, 'd' },
	{ "debug", required_argument, NULL, 'g' },
	{ "help", 0, NULL, 'h' },
	{ "version", 0, NULL, 'v' },
	{ NULL, 0, NULL, 0 }
};

static char *shortopts = "m:d:g:hv";

static void
print_usage(void)
{
	puts(
		_("Usage: comard [OPTIONS]\n"
		"Pardus configuration manager.\n"
		" -m, --model [FILE]  Use the given xml model file.\n"
		" -d, --datadir [DIR] Data storage directory.\n"
		" -g, --debug [FLAGS] Enable debug output.\n"
		" -h, --help          Print this text and exit.\n"
		" -v, --version       Print version and exit.\n"
		"Report bugs to http://bugs.uludag.org.tr")
	);
}

static void
print_version(void)
{
	printf(
		_("COMARd %s\n"
		"Copyright (c) 2005, TUBITAK/UEKAE\n"
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
				cfg_model_file = optarg;
				break;
			case 'd':
				cfg_data_dir = optarg;
				break;
			case 'g':
				for (j = 0; logflags[j].flag; ++j) {
					if (strstr(optarg, logflags[j].flag))
						cfg_log_flags |= logflags[j].value;
				}
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
