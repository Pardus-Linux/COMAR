/*
** Copyright (c) 2004, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - csl-edit.c
** csl editor widget
*/

#include "common.h"
#include "csl-edit.h"

static GtkSourceTagTable *tag_table;

static void
csl_edit_class_init(CSLEditClass *class)
{
	GSList *tag_list = NULL, *keys = NULL;
	GtkTextTag *tag;
	GtkSourceTagStyle *style;

	tag = gtk_line_comment_tag_new ("CSLComment", "CSLCo", "#");
	style = gtk_source_tag_style_new ();
	style->mask = GTK_SOURCE_TAG_STYLE_USE_FOREGROUND;
	gdk_color_parse ("#ff0000", &style->foreground);
	gtk_source_tag_set_style (GTK_SOURCE_TAG (tag), style);
	tag_list = g_slist_prepend (tag_list, tag);

	tag = gtk_string_tag_new ("CSLString", "CSLSt", "\"", "\"", FALSE);
	style = gtk_source_tag_style_new ();
	style->mask = GTK_SOURCE_TAG_STYLE_USE_FOREGROUND;
	gdk_color_parse ("#097e07", &style->foreground);
	gtk_source_tag_set_style (GTK_SOURCE_TAG (tag), style);
	tag_list = g_slist_prepend (tag_list, tag);

	keys = g_slist_prepend (keys, "method");
	keys = g_slist_prepend (keys, "property");
	keys = g_slist_prepend (keys, "get");
	keys = g_slist_prepend (keys, "set");
	keys = g_slist_prepend (keys, "persistent");
	keys = g_slist_prepend (keys, "instance");
	keys = g_slist_prepend (keys, "makeinstance");
	keys = g_slist_prepend (keys, "exit");
	keys = g_slist_prepend (keys, "abort");
	keys = g_slist_prepend (keys, "if");
	keys = g_slist_prepend (keys, "elif");
	keys = g_slist_prepend (keys, "else");
	keys = g_slist_prepend (keys, "while");
	keys = g_slist_prepend (keys, "for");
	keys = g_slist_prepend (keys, "foreach");
	keys = g_slist_prepend (keys, "in");
	keys = g_slist_prepend (keys, "break");
	keys = g_slist_prepend (keys, "pass");
	keys = g_slist_prepend (keys, "and");
	keys = g_slist_prepend (keys, "or");
	keys = g_slist_prepend (keys, "not");
	tag = gtk_keyword_list_tag_new ("CSLFunction", "CSLFu", keys,
		TRUE, TRUE, TRUE, NULL, NULL);
	style = gtk_source_tag_style_new ();
	style->mask = GTK_SOURCE_TAG_STYLE_USE_FOREGROUND;
	gdk_color_parse ("#0000ff", &style->foreground);
	gtk_source_tag_set_style (GTK_SOURCE_TAG (tag), style);
	tag_list = g_slist_prepend (tag_list, tag);

	tag_table = gtk_source_tag_table_new ();
	gtk_source_tag_table_add_tags (tag_table, tag_list);
}

static void
ce_message(CSLEdit *cew, char *fmt, ...)
{
	va_list ap;
	char *tmp;

	va_start(ap, fmt);
	tmp = g_strdup_vprintf(fmt, ap);
	va_end(ap);
	gtk_statusbar_push(GTK_STATUSBAR(cew->status), cew->status_id, tmp);
	g_free(tmp);
}

static void
csl_edit_open(char *name, gpointer data)
{
	CSLEdit *obj = (CSLEdit *) data;
	GtkTextIter start, end;
	gchar *tmp;

	if (g_file_get_contents (name, &tmp, NULL, NULL) != TRUE) {
		ce_message (obj, _("Cannot open '%s' !"), name);
		// bork bork
		return;
	}

	gtk_text_buffer_get_bounds (GTK_TEXT_BUFFER (obj->sbuf), &start, &end);
	gtk_text_buffer_delete (GTK_TEXT_BUFFER (obj->sbuf), &start, &end);
	gtk_text_buffer_insert (GTK_TEXT_BUFFER (obj->sbuf), &start, tmp, -1);
	g_free (tmp);
}

static void
csl_edit_save(char *name, gpointer data)
{
	CSLEdit *cew = (CSLEdit *) data;
	GtkTextIter iter1, iter2;
	char *text;
	FILE *f;

	gtk_text_buffer_get_bounds (GTK_TEXT_BUFFER (cew->sbuf), &iter1, &iter2);
	text = gtk_text_buffer_get_text (GTK_TEXT_BUFFER (cew->sbuf), &iter1, &iter2, FALSE);
	f = fopen (name, "w");
	if (!f) {
		ce_message (cew, _("Cannot save '%s' !"), name);
		// bork bork
		return;
	}
	fwrite (text, 1, strlen (text), f); // FIXME: hata kontrolu
	fclose (f);
}

static void
cb_save_as(CSLEdit *cew)
{
	GtkWidget *t;

	t = main_window;
	main_window = GTK_WIDGET (cew);
	select_file (TRUE, _("Select CSL Script As ..."), csl_edit_save, cew);
	main_window = t;
}

static void
cb_open(CSLEdit *cew)
{
	GtkWidget *t;

	t = main_window;
	main_window = GTK_WIDGET (cew);
	select_file (FALSE, _("Open a CSL Script ..."), csl_edit_open, cew);
	main_window = t;
}

static void
cb_close(CSLEdit *cew)
{
	gtk_widget_destroy (GTK_WIDGET (cew));
}

static void
csl_edit_init(CSLEdit *obj)
{
	GtkItemFactoryEntry menus[] = {
		{ _("/_File"), NULL, NULL, 0, "<Branch>" },
		{ _("/File/_Open ..."), "", cb_open, 0, "<StockItem>", GTK_STOCK_OPEN },
		{ _("/File/Save _As ..."), "", cb_save_as, 0, "<StockItem>", GTK_STOCK_SAVE_AS },
		{ _("/File/separator"), NULL, NULL, 0, "<Separator>" },
		{ _("/File/_Close"), NULL, cb_close, 0, "<StockItem>", GTK_STOCK_CLOSE },
	};
	GtkItemFactory *factory;
	GtkAccelGroup *agrp;
	gint n = sizeof (menus) / sizeof (menus[0]);
	GtkWindow *w;
	GtkWidget *vb, *menu, *sw;
	GtkSourceBuffer *sbuf;

	w = &obj->window;
	gtk_window_set_title (w, _("CSL Editor"));
	gtk_window_set_default_size (w, 600, 340);
	g_signal_connect (w, "delete_event", G_CALLBACK (gtk_widget_destroy), NULL);

	vb = gtk_vbox_new (FALSE, 0);
	gtk_widget_show (vb);
	gtk_container_add (GTK_CONTAINER (w), vb);

	// menu
	agrp = gtk_accel_group_new ();
	factory = gtk_item_factory_new (GTK_TYPE_MENU_BAR, "<main>", agrp);
	gtk_item_factory_create_items (factory, n, menus, w);
	gtk_window_add_accel_group (GTK_WINDOW (w), agrp);
	menu = gtk_item_factory_get_widget (factory, "<main>");
	gtk_widget_show (menu);
	gtk_box_pack_start (GTK_BOX (vb), menu, FALSE, FALSE, 0);

	// edit alanı
	sw = gtk_scrolled_window_new (NULL, NULL);
	gtk_widget_show (sw);
	gtk_scrolled_window_set_shadow_type (GTK_SCROLLED_WINDOW (sw), GTK_SHADOW_ETCHED_IN);
	gtk_scrolled_window_set_policy (GTK_SCROLLED_WINDOW (sw), GTK_POLICY_AUTOMATIC, GTK_POLICY_ALWAYS);
	gtk_box_pack_start (GTK_BOX (vb), sw, TRUE, TRUE, 0);

	sbuf = gtk_source_buffer_new (tag_table);
	obj->sbuf = sbuf;
	gtk_source_buffer_set_escape_char (sbuf, '\\');
	gtk_source_buffer_set_highlight (sbuf, TRUE);

{
	GtkSourceTagStyle *style;

	style = gtk_source_tag_style_new ();
	style->mask = GTK_SOURCE_TAG_STYLE_USE_FOREGROUND;
	gdk_color_parse ("#ff0000", &style->foreground);
	style->bold = TRUE;
	gtk_source_buffer_set_bracket_match_style (sbuf, style);
}

	obj->source_view = gtk_source_view_new_with_buffer (sbuf);
	gtk_widget_show (obj->source_view);
	gtk_container_add (GTK_CONTAINER (sw), obj->source_view);

	// status bar
	obj->status = gtk_statusbar_new ();
	obj->status_id = gtk_statusbar_get_context_id (GTK_STATUSBAR (obj->status), "csl_edit");
	gtk_widget_show (obj->status);
	gtk_box_pack_start (GTK_BOX (vb), obj->status, FALSE, FALSE, 0);
}

GType
csl_edit_get_type(void)
{
	static GType csl_edit_type = 0;

	if (!csl_edit_type) {
		static const GTypeInfo csl_edit_info = {
			sizeof (CSLEditClass),
			NULL,
			NULL,
			(GClassInitFunc) csl_edit_class_init,
			NULL,
			NULL,
			sizeof (CSLEdit),
			0,
			(GInstanceInitFunc) csl_edit_init
		};
		csl_edit_type = g_type_register_static(GTK_TYPE_WINDOW, "CSLEdit", &csl_edit_info, 0);
	}
	return csl_edit_type;
}

GtkWidget *
csl_edit_new(void)
{
	return GTK_WIDGET(g_object_new(csl_edit_get_type(), NULL));
}

static void
csl_edit_append(GtkWidget *cew, const char *fmt, ...)
{
	va_list ap;
	CSLEdit *obj;
	GtkTextIter iter;
	char *tmp;

	obj = (CSLEdit *) cew;
	gtk_text_buffer_get_end_iter (GTK_TEXT_BUFFER (obj->sbuf), &iter);
	va_start (ap, fmt);
	tmp = g_strdup_vprintf (fmt, ap);
	gtk_text_buffer_insert (GTK_TEXT_BUFFER (obj->sbuf), &iter, tmp, -1);
	g_free (tmp);
	va_end (ap);
}

void
csl_template(iks *x)
{
	GtkWidget *w;
	iks *y;

	w = csl_edit_new();
	if (!x) goto out;

	for (y = iks_first_tag(x); y; y = iks_next(y)) {
		if (iks_strcmp(iks_name(y), "method") == 0) {
			csl_edit_append(w, "method %s {\n\n}\n", iks_find_attrib(y, "name"));
		} else if (iks_strcmp(iks_name(y), "property") == 0) {
			csl_edit_append(w, "property %s {\n", iks_find_attrib(y, "name"));
			csl_edit_append(w, "	get {\n		\n	}\n");
			csl_edit_append(w, "	set {\n		\n	}\n");
			csl_edit_append(w, "}\n");
		}
		csl_edit_append (w, "\n");
	}

out:
	gtk_widget_show(w);
}

void
csl_open (void)
{
	GtkWidget *w;

	w = csl_edit_new ();
	gtk_widget_show (w);
	cb_open ((CSLEdit *)w);
}
