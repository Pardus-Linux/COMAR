/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - node-desc.c
** node description editor widget
*/

#include "common.h"
#include "node-desc.h"

static void
node_desc_class_init(NodeDescClass *class)
{
}

static gboolean
cb_change_desc(GtkWidget *w, GdkEventFocus *ev, NodeDesc *obj)
{
	GtkTextIter iter1, iter2;
	char *text, *old;
	iks *y;

	gtk_text_buffer_get_bounds(obj->desc_buf, &iter1, &iter2);
	text = gtk_text_buffer_get_text(obj->desc_buf, &iter1, &iter2, FALSE);
	if (obj->x) {
		y = iks_find(obj->x, "description");
		old = iks_cdata(iks_child(y));
		if (old) {
			if (iks_strcmp(old, text) == 0) goto out;
			iks_hide(y);
		}
		iks_insert_cdata(iks_insert(obj->x, "description"), text, 0);
	}
out:
	g_free(text);
	return FALSE;
}

static void
node_desc_init(NodeDesc *obj)
{
	GtkWidget *lab, *sw, *b;

	obj->x = NULL;

	lab = gtk_label_new(_("Description:"));
	gtk_misc_set_alignment(GTK_MISC(lab), 0, 0);
	gtk_widget_show(lab);
	gtk_box_pack_start(GTK_BOX(obj), lab, FALSE, TRUE, 0);

	sw = gtk_scrolled_window_new(NULL, NULL);
	gtk_widget_show(sw);
	gtk_scrolled_window_set_shadow_type(GTK_SCROLLED_WINDOW(sw), GTK_SHADOW_ETCHED_IN);
	gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(sw), GTK_POLICY_NEVER, GTK_POLICY_ALWAYS);
	gtk_box_pack_start(GTK_BOX(obj), sw, TRUE, TRUE, 0);

	b = gtk_text_view_new();
	gtk_widget_show(b);
	gtk_text_view_set_wrap_mode(GTK_TEXT_VIEW(b), GTK_WRAP_CHAR);
	gtk_container_add(GTK_CONTAINER(sw), b);
	obj->desc_buf = gtk_text_view_get_buffer(GTK_TEXT_VIEW(b));
	g_signal_connect(G_OBJECT(b), "focus-out-event", G_CALLBACK (cb_change_desc), obj);
}

GType
node_desc_get_type(void)
{
	static GType node_desc_type = 0;

	if (!node_desc_type) {
		static const GTypeInfo node_desc_info = {
			sizeof (NodeDescClass),
			NULL,
			NULL,
			(GClassInitFunc) node_desc_class_init,
			NULL,
			NULL,
			sizeof (NodeDesc),
			0,
			(GInstanceInitFunc) node_desc_init
		};
		node_desc_type = g_type_register_static(GTK_TYPE_VBOX, "NodeDesc", &node_desc_info, 0);
	}
	return node_desc_type;
}

GtkWidget *
node_desc_new(void)
{
	return GTK_WIDGET(g_object_new(node_desc_get_type(), NULL));
}

void
node_desc_edit(GtkWidget *w, iks *x)
{
	NodeDesc *obj = (NodeDesc *) w;
	char *desc;

	if (obj->x) cb_change_desc(NULL, NULL, obj);
	obj->x = x;

	desc = iks_find_cdata(x, "description");
	if (desc) {
		gtk_text_buffer_set_text(obj->desc_buf, desc, -1);
	} else {
		gtk_text_buffer_set_text(obj->desc_buf, "", 0);
	}
}
