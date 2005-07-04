/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

struct node {
	const char *name;
	int no;
};

int
model_init(void)
{
	return 0;
}

int
model_lookup_node(const char *node)
{
}

int
model_has_method(int node_no, const char *method)
{
}
