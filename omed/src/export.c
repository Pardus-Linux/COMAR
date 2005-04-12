/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - export.c
** lyx document exporter
*/

#include "common.h"

static FILE *exp_f;

static void
print_preamble(void)
{
	fputs(
		"#LyX 1.3 created this file. For more info see http://www.lyx.org/\n"
		"\\lyxformat 221\n"
		"\\textclass article\n"
		"\\begin_preamble\n"
		"\\tolerance=10000\n"
		"\\usepackage{indentfirst}\n"
		"\\end_preamble\n"
		"\\language turkish\n"
		"\\inputencoding auto\n"
		"\\fontscheme pslatex\n"
		"\\graphics default\n"
		"\\paperfontsize default\n"
		"\\spacing single \n"
		"\\papersize Default\n"
		"\\paperpackage a4\n"
		"\\use_geometry 0\n"
		"\\use_amsmath 0\n"
		"\\use_natbib 0\n"
		"\\use_numerical_citations 0\n"
		"\\paperorientation portrait\n"
		"\\secnumdepth 3\n"
		"\\tocdepth 3\n"
		"\\paragraph_separation skip\n"
		"\\defskip medskip\n"
		"\\quotes_language english\n"
		"\\quotes_times 2\n"
		"\\papercolumns 1\n"
		"\\papersides 1\n"
		"\\paperpagestyle default\n"
		"\n",
		exp_f
	);
}

static void
print_title(char *title, char *author)
{
	fprintf(exp_f, "\\layout Title\n\n%s\n", my_iconv(title));
	fprintf(exp_f, "\\layout Author\n\n%s\n", my_iconv(author));
}

static void
print_node(int level, char *name, char *desc)
{
	const char *sect;

	switch (level) {
		case 0: sect = "Section"; break;
		case 1: sect = "Subsection"; break;
		case 2: sect = "Subsubsection"; break;
		default:
			sect = "Subsubsection";
	}
	fprintf(exp_f, "\\layout %s\n\n%s\n", sect, my_iconv(name));
	if (desc) fprintf(exp_f, "\\layout Quote\n\n%s\n", my_iconv(desc));
}

static void
print_end(void)
{
	fputs("\\the_end\n\n", exp_f);
}

static void
print_methods(void)
{
	fputs("\\layout Standart\n\n\n\\series bold\nMetotlar:\n\n", exp_f);
}

static void
print_properties(void)
{
	fprintf(exp_f, "\\layout Standart\n\n\n\\series bold\n%s\n",
		my_iconv("Öznitelikler:"));
}

static void
print_tabular(int cnt)
{
	printf(
		"\\layout Quote\n\n\n"
		"\\begin_inset  Tabular\n"
		"<lyxtabular version=\"3\" rows=\"%d\" columns=\"2\">\n"
		"<features>\n"
		"<column alignment=\"left\" valignment=\"top\" leftline=\"true\" width=\"0\">\n"
		"<column alignment=\"left\" valignment=\"top\" leftline=\"true\" rightline=\"true\" width=\"0\">\n",
		cnt
	);
}

static void
print_attr_head(char *title)
{
	printf(
		"<row topline=\"true\" bottomline=\"true\">\n"
		"<cell multicolumn=\"1\" alignment=\"center\" valignment=\"top\" topline=\"true\" bottomline=\"true\" leftline=\"true\" rightline=\"true\" usebox=\"none\">\n"
		"\\begin_inset Text\n"
		"\n"
		"\\layout Standard\n"
		"\n"
		"%s\n"
		"\\end_inset\n"
		"</cell>\n"
		"<cell multicolumn=\"2\" alignment=\"center\" valignment=\"top\" topline=\"true\" leftline=\"true\" rightline=\"true\" usebox=\"none\">\n"
		"\\begin_inset Text\n"
		"\n"
		"\\layout Standard\n"
		"\n"
		"\\end_inset\n"
		"</cell>\n"
		"</row>\n",
		my_iconv(title)
	);
}

static void
print_attr(char *name, char *desc)
{
	char *d;

	if (desc) d = strdup(my_iconv(desc)); else d = "";
	printf(
		"<row bottomline=\"true\">\n"
		"<cell alignment=\"left\" valignment=\"top\" topline=\"true\" bottomline=\"true\" leftline=\"true\" rightline=\"true\" usebox=\"none\">\n"
		"\\begin_inset Text\n"
		"\n"
		"\\layout Standard\n"
		"\n"
		"%s\n"
		"\\end_inset\n"
		"</cell>\n"
		"<cell alignment=\"left\" valignment=\"top\" topline=\"true\" leftline=\"true\" rightline=\"true\" usebox=\"none\">\n"
		"\\begin_inset Text\n"
		"\n"
		"\\layout Standard\n"
		"\n"
		"%s\n"
		"\\end_inset\n"
		"</cell>\n"
		"</row>\n",
		my_iconv(name),
		d
	);
	if (d) free(d);
}

static int
count_tag(iks *parent, char *name)
{
	iks *x;
	int cnt = 0;

	if (!parent) return 0;
	for (x = iks_first_tag(parent); x; x = iks_next_tag(x)) {
		if (strcmp(iks_name(x), name) == 0) cnt++;
	}
	return cnt;
}

void
export_attributes(iks *class)
{
	iks *x, *attrs, *methods;
	int attrs_cnt, methods_cnt;

	attrs = iks_find(class, "attributes");
	attrs_cnt = count_tag(attrs, "attr");

	methods = iks_find(class, "methods");
	methods_cnt = count_tag(methods, "method");

	if (0 == attrs_cnt + methods_cnt) return;

	// başlıklar
	if (attrs_cnt) attrs_cnt++;
	if (methods_cnt) methods_cnt++;

	print_tabular(attrs_cnt + methods_cnt);

	if (attrs_cnt) {
		print_attr_head("Özellikler");
		for (x = iks_first_tag(attrs); x; x = iks_next_tag(x)) {
			if (strcmp(iks_name(x), "attr") == 0) {
				print_attr(iks_find_attrib(x, "name"), iks_find_cdata(x, "desc"));
			}
		}
	}

	if (methods_cnt) {
		print_attr_head("Metotlar");
		for (x = iks_first_tag(methods); x; x = iks_next_tag(x)) {
			if (strcmp(iks_name(x), "method") == 0) {
				print_attr(iks_find_attrib(x, "name"), iks_find_cdata(x, "desc"));
			}
		}
	}

	puts("</lyxtabular>");
	puts("\\end_inset");
}

static void
print_desc(char *desc)
{
	char *tmp, *s;

	tmp = g_strdup(desc);
	s = strtok(tmp, "\r\n");
	while (s) {
		fprintf(exp_f, "\\layout Standart\n\n%s\n", my_iconv(s));
		s = strtok(NULL, "\r\n");
	}
}

static void
export_method(iks *method)
{
	char *desc;

	fprintf(exp_f, "\\layout Itemize\n\n\\series Bold\n\n%s\n",
		my_iconv(iks_find_attrib(method, "name")));
	desc = iks_find_cdata(method, "description");
	if (desc) print_desc(desc);
}

static void
export_property(iks *prop)
{
	char *desc;

	fprintf(exp_f, "\\layout Itemize\n\n\\series Bold\n\n%s\n",
		my_iconv(iks_find_attrib(prop, "name")));
	desc = iks_find_cdata(prop, "description");
	if (desc) print_desc(desc);
}

static int node_level;

static void
export_node(iks *node)
{
	iks *x;

	print_node(node_level, iks_find_attrib(node, "name"), iks_find_cdata(node, "description"));

	if (iks_find(node, "method")) {
		print_methods();
		for (x = iks_first_tag(node); x; x = iks_next(x)) {
			if (strcmp(iks_name(x), "method") == 0) {
				export_method(x);
			}
		}
	}
	if (iks_find(node, "property")) {
		print_properties();
		for (x = iks_first_tag(node); x; x = iks_next(x)) {
			if (strcmp(iks_name(x), "property") == 0) {
				export_property(x);
			}
		}
	}
	for (x = iks_first_tag(node); x; x = iks_next(x)) {
		if (strcmp(iks_name(x), "object") == 0) {
//			fputs ("\\begin_deeper \n", exp_f);
			node_level++;
			export_node(x);
			node_level--;
//			fputs ("\\end_deeper \n", exp_f);
		}
	}
}

static void
export_namespace(iks *ns)
{
	iks *x;

	node_level = 0;
	for (x = iks_first_tag(ns); x; x = iks_next_tag(x)) {
		if (strcmp(iks_name(x), "object") == 0) {
			export_node(x);
		}
	}
}

void
export_lyx(iks *doc, const char *file_name)
{
	iks *root;

	exp_f = fopen(file_name, "w");
	if (!exp_f) {
		message_box("Cannot export LyX file!");
		return;
	}

	print_preamble();
	root = iks_find(doc, "namespace");

	print_title(iks_find_attrib (root, "name"), "Dürtücü Teknolociler ArGe Labs.");
	export_namespace(root);

	print_end();

	fclose(exp_f);
	ui_message("Exported.");
}
