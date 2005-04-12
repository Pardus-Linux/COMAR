/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - ui-util.c
** utility functions for gtk
*/

#include "common.h"

static GtkTooltips *tips;

void
tip_attach (GtkWidget *w, const char *tip)
{
	if (!tips) tips = gtk_tooltips_new ();
	gtk_tooltips_set_tip (GTK_TOOLTIPS (tips), w, tip, NULL);
}

GtkWidget *
pix_button (const char *stock_id, char *tip)
{
	GtkWidget *b, *img;

	b = gtk_button_new ();
	gtk_widget_show (b);

	img = gtk_image_new ();
	gtk_widget_show (img);
	gtk_image_set_from_stock (GTK_IMAGE (img), stock_id, GTK_ICON_SIZE_BUTTON);
	gtk_container_add (GTK_CONTAINER (b), img);

	tip_attach (b, tip);
	return b;
}

GtkWidget *
right_label (char *text)
{
	GtkWidget *align, *lab;

	align = gtk_alignment_new (0.9, 0.5, 0, 0);
	gtk_widget_show (align);
	lab = gtk_label_new (text);
	gtk_widget_show (lab);
	gtk_container_add (GTK_CONTAINER (align), lab);
	return align;
}

static void
cb_msgbox (GtkDialog *dialog, gint arg1, char *msg)
{
	g_free (msg);
	gtk_widget_destroy (GTK_WIDGET (dialog));
}

void
message_box (char *fmt, ...)
{
	va_list ap;
	char *msg;
	GtkWidget *dialog;

	va_start (ap, fmt);
	msg = g_strdup_vprintf (fmt, ap);
	va_end (ap);
	dialog = gtk_message_dialog_new (
		GTK_WINDOW (main_window),
		GTK_DIALOG_DESTROY_WITH_PARENT,
		GTK_MESSAGE_ERROR,
		GTK_BUTTONS_CLOSE,
		msg
	);
	gtk_widget_show (dialog);
	g_signal_connect (dialog, "response", G_CALLBACK (cb_msgbox), msg);
}

static void
cb_filesel (GtkDialog *dialog, gint arg1, void (*func)(char *filename, gpointer data))
{
	char *name;
	gpointer data;

	if (arg1 == GTK_RESPONSE_ACCEPT) {
		name = gtk_file_chooser_get_filename (GTK_FILE_CHOOSER (dialog));
		data = g_object_get_data (G_OBJECT (dialog), "data");
		func (name, data);
		g_free (name);
	}
	gtk_widget_destroy (GTK_WIDGET (dialog));
}

void
select_file (gboolean for_save, char *title, void (*func)(char *filename, gpointer data), gpointer data)
{
	GtkWidget *dialog;
	GtkFileChooserAction mode;

	if (for_save)
		mode = GTK_FILE_CHOOSER_ACTION_SAVE;
	else
		mode = GTK_FILE_CHOOSER_ACTION_OPEN;

	dialog = gtk_file_chooser_dialog_new (
		title,
		GTK_WINDOW (main_window),
		mode,
		GTK_STOCK_CANCEL, GTK_RESPONSE_CANCEL,
		for_save ? GTK_STOCK_SAVE : GTK_STOCK_OPEN, GTK_RESPONSE_ACCEPT,
		NULL
	);
	g_object_set_data (G_OBJECT (dialog), "data", data);
	gtk_widget_show (dialog);
	g_signal_connect (dialog, "response", G_CALLBACK (cb_filesel), func);
}
