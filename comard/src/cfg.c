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
#include "cfg.h"

/* global option variables with defaults */
// FIXME: test only, proper defaults are given in comments
char *cfg_model_file = "model.xml";	// /etc/comar/system_model.xml
char *cfg_data_dir = "db"; // /var/lib/comar
int cfg_log_console = 1;	// 0
int cfg_log_file = 0;
char *cfg_log_file_name = "log.txt";

static struct option longopts[] = {
	{ "model", required_argument, NULL, 'm' },
	{ "datadir", required_argument, NULL, 'd' },
	{ "help", 0, NULL, 'h' },
	{ "version", 0, NULL, 'v' },
	{ NULL, 0, NULL, 0 }
};

static char *shortopts = "m:d:hv";

static void
print_usage(void)
{
	puts(
		_("Usage: comard [OPTIONS]\n"
		"Pardus configuration manager.\n"
		" -m, --model [FILE]  Use the given xml model file.\n"
		" -d, --datadir [DIR] Data storage directory.\n"
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
	int c, i;

	while ((c = getopt_long(argc, argv, shortopts, longopts, &i)) != -1) {
		switch (c) {
			case 'm':
				cfg_model_file = optarg;
				break;
			case 'd':
				cfg_data_dir = optarg;
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
