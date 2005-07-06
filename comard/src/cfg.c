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

/* possible options:
	database dir, model file, daemon mode, log/debug output
*/

static struct option longopts[] = {
	{ "help", 0, 0, 'h' },
	{ "version", 0, 0, 'v' },
	{ 0, 0, 0, 0 }
};

static char *shortopts = "hv";

static void
print_usage(void)
{
	puts(
		"Usage: comard [OPTIONS]\n"
		"Pardus configuration manager.\n"
		" -h, --help          Print this text and exit.\n"
		" -v, --version       Print version and exit.\n"
		"Report bugs to http://bugs.uludag.org.tr"
	);
}

void
cfg_init(int argc, char *argv[])
{
	int c, i;

	while ((c = getopt_long(argc, argv, shortopts, longopts, &i)) != -1) {
		switch (c) {
			case 'h':
				print_usage();
				exit(0);
			case 'v':
				puts("COMARd "VERSION);
				exit(0);
		}
	}
}
