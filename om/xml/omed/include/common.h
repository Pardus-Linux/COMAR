/*
** Copyright (c) 2004, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - common.h
** global macros and definitions
*/

#ifndef COMMON_H
#define COMMON_H 1

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <sys/types.h>
#include <stdio.h>

#ifdef STDC_HEADERS
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#elif HAVE_STRINGS_H
#include <strings.h>
#endif

#ifdef HAVE_UNISTD_H
#include <unistd.h>
#endif

#ifdef HAVE_ERRNO_H
#include <errno.h>
#endif
#ifndef errno
extern int errno;
#endif

#include <gtk/gtk.h>
#include <iksemel.h>
#include "i18n.h"
#include "om-tree.h"
#include "om-node.h"

extern GtkWidget *main_window;

void ui_setup (void);
void ui_add_node (int type, char *name);
iks *ui_serialize_om (void);
void ui_message (char *msg);
void ui_open (char *file, gpointer data);

void tip_attach (GtkWidget *w, const char *tip);
GtkWidget *right_label (char *text);
GtkWidget *pix_button (const char *stock_id, char *text);
void message_box (char *fmt, ...);
void select_file (gboolean for_save, char *title, void (*func)(char *filename, gpointer data), gpointer data);

GtkCellRenderer *gtk_cell_combo (int nr, ...);

void export_lyx (iks *doc, const char *file_name);

char *my_iconv (char *text);



#endif	/* COMMON_H */
