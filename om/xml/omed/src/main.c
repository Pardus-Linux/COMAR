/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - main.c
** main() entry point
*/

#include "common.h"

#ifdef HAVE_GETOPT_LONG
#include <getopt.h>

static struct option longopts[] = {
	{ "help", 0, 0, 'h' },
	{ "version", 0, 0, 'v' },
	{ 0, 0, 0, 0 }
};
#endif

static char *shortopts = "hv";

static void
print_usage (void)
{
	puts (_("Usage: omed [OPTIONS] FILE\n"
		"COMAR OM Editor.\n"
		" -h, --help     Print this text and exit.\n"
		" -v, --version  Print version and exit."));
#ifndef HAVE_GETOPT_LONG
	printf (_("(long options are not supported on your system)\n"));
#endif
	puts (_("Report bugs to <gurer@uludag.org.tr>."));
}

int
main (int argc, char *argv[])
{
	int c;
#ifdef HAVE_GETOPT_LONG
	int i;
#endif

	bindtextdomain (PACKAGE, LOCALEDIR);
	bind_textdomain_codeset (PACKAGE, "UTF-8");
	textdomain (PACKAGE);

#ifdef HAVE_GETOPT_LONG
	while ((c = getopt_long (argc, argv, shortopts, longopts, &i)) != -1) {
#else
	while ((c = getopt (argc, argv, shortopts)) != -1) {
#endif
		switch (c) {
			case 'h':
				print_usage ();
				exit (0);
			case 'v':
				puts ("omed "VERSION);
				exit (0);
		}
	}

	gtk_init (&argc, &argv);
	ui_setup ();

	if (optind < argc) {
		if (strcmp (argv[optind], "moo") == 0) {
			/*  8')  */
			puts (_("I don't have any easter eggs... or do I?"));
			exit (0);
		} else {
			ui_open (argv[optind], NULL);
		}
	}

	gtk_main ();

	return 0;
}
