/*
** Copyright (c) 2004, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** comar-call - main.c
** sends om calls over unix rpc to comard
*/

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stddef.h>
#include <stdarg.h>
#include <getopt.h>
#include <sys/stat.h>

#include "rpc.h"

static struct option longopts[] = {
	{ "help", 0, 0, 'h' },
	{ "version", 0, 0, 'v' },
	{ "wait", 0, 0, 'w' },
	{ 0, 0, 0, 0 }
};
static char *shortopts = "hvw";

void
print_usage(void)
{
	puts(
		"usage: comar-call [options] <command> [args]\n"
		"commands:\n"
		"   method <om-method-name> [parameter=value]...\n"
		"   register <om-object-name> <csl-file>\n"
		"options:\n"
		"   -w, --wait\n"
		"report bugs to <gurer@uludag.org.tr>"
	);
}

unsigned char *
load_file(const char *fname)
{
	FILE *f;
	struct stat fs;
	size_t size;
	unsigned char *data;

	if (stat(fname, &fs) != 0) {
		printf("Cannot stat file '%s'\n", fname);
		exit(2);
	}
	size = fs.st_size;
	data = malloc(size + 1);
	if (!data) {
		printf("Cannot allocate %d bytes for file buffer\n", size);
		exit(2);
	}
	f = fopen(fname, "rb");
	if (!f) {
		printf("Cannot open file '%s'\n", fname);
		exit(2);
	}
	if (fread(data, size, 1, f) < 1) {
		printf("Read error in file '%s'\n", fname);
		exit(2);
	}
	fclose(f);
	data[size] = '\0';
	return data;
}

int
main(int argc, char *argv[])
{
	int c, i, ret;
	int opt_wait = 0;
	char *cmd;

	while ((c = getopt_long(argc, argv, shortopts, longopts, &i)) != -1) {
		switch (c) {
			case 'h':
				print_usage();
				exit(0);
			case 'v':
				puts("comar-call 1.0");
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

	i = 0;
	while (i < 15) {
		ret = rpc_connect();
		if (ret == 0) break;
		i++;
		sleep(1);
	}
	if (ret != 0) {
		puts("COMAR nerede?");
		exit(1);
	}
	if (strcmp(cmd, "method") == 0) {
		char *args, *node, *rpcdata, *t;
		node = argv[optind++];
		args = NULL;
		while (optind < argc) {
			t = strchr(argv[optind], '=');
			if (!t) {
				print_usage();
				exit(1);
			}
			*t = '\0';
			t++;
			args = rpc_add_string(args, argv[optind], t);
			optind++;
		}
		rpcdata = rpc_make_call(RPC_METHOD, node, args);
		if (opt_wait)
			rpc_send(RPC_OMCALL | RPC_INTERACTIVE, "hede", rpcdata);
		else
			rpc_send(RPC_OMCALL | RPC_DONTCARE, "hede", rpcdata);
		free(rpcdata);
	} else if (strcmp(cmd, "register") == 0) {
		char *args, *node, *script, *rpcdata;
		if (argc - optind > 2) {
			print_usage();
			exit(1);
		}
		node = argv[optind++];
		script = load_file(argv[optind]);
		//
		args = rpc_add_string(NULL, "node", node);
		args = rpc_add_string(args, "AppID", "UI");
		// FIXME: dosya adinin sadece son kismi ile kaydet
		args = rpc_add_string(args, "fileName", argv[optind]);
		args = rpc_add_string(args, "code", script);
		args = rpc_add_string(args, "language", "CSL");
		//
		rpcdata = rpc_make_call(RPC_METHOD, "CORE:om.addNodeScript", args);
		if (opt_wait)
			rpc_send(RPC_OMCALL | RPC_INTERACTIVE, "hede", rpcdata);
		else
			rpc_send(RPC_OMCALL | RPC_DONTCARE, "hede", rpcdata);
		free(rpcdata);
		free(script);
	} else {
		print_usage();
		exit(1);
	}

	if (opt_wait) {
		rpc_recv();
	}

	rpc_disconnect();

	return 0;
}
