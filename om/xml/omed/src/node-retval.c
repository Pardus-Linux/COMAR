/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - node-retval.c
** return value widget
*/

#include "common.h"
#include "node-retval.h"

static void
node_retval_class_init(NodeRetvalClass *class)
{
}

static void
node_retval_init(NodeRetval *obj)
{
	GtkWidget *hb, *b;

	hb = gtk_hbox_new(FALSE, 6);
	gtk_widget_show(hb);
	gtk_box_pack_start(GTK_BOX(obj), hb, FALSE, FALSE, 0);

	b = gtk_label_new(_("Return value:"));
	gtk_widget_show(b);
	gtk_box_pack_start(GTK_BOX(hb), b, FALSE, FALSE, 0);

	obj->combo = gtk_combo_box_new_text();
	gtk_combo_box_append_text(GTK_COMBO_BOX(obj->combo), _("None"));
	gtk_combo_box_append_text(GTK_COMBO_BOX(obj->combo), _("String"));
	gtk_combo_box_append_text(GTK_COMBO_BOX(obj->combo), _("Integer"));
	gtk_combo_box_append_text(GTK_COMBO_BOX(obj->combo), _("Array"));
	gtk_combo_box_append_text(GTK_COMBO_BOX(obj->combo), _("Object"));
	gtk_widget_show(obj->combo);
	gtk_box_pack_start(GTK_BOX(hb), obj->combo, FALSE, FALSE, 0);

	obj->rw_label = gtk_label_new(_("access:"));
	gtk_widget_show(obj->rw_label);
	gtk_box_pack_start(GTK_BOX(hb), obj->rw_label, FALSE, FALSE, 0);

	obj->rw_combo = gtk_combo_box_new_text();
	gtk_combo_box_append_text(GTK_COMBO_BOX(obj->rw_combo), _("Read/Write"));
	gtk_combo_box_append_text(GTK_COMBO_BOX(obj->rw_combo), _("Read only"));
	gtk_combo_box_append_text(GTK_COMBO_BOX(obj->rw_combo), _("Write only"));
	gtk_widget_show(obj->rw_combo);
	gtk_box_pack_start(GTK_BOX(hb), obj->rw_combo, FALSE, FALSE, 0);

	obj->loc = gtk_check_button_new_with_label(_("Localized"));
	gtk_widget_show(obj->loc);
	gtk_box_pack_start(GTK_BOX(hb), obj->loc, FALSE, FALSE, 0);

	b = gtk_label_new("");
	gtk_widget_show(b);
	gtk_box_pack_start(GTK_BOX(hb), b, TRUE, FALSE, 0);

}

GType
node_retval_get_type(void)
{
	static GType node_retval_type = 0;

	if (!node_retval_type) {
		static const GTypeInfo node_retval_info = {
			sizeof (NodeRetvalClass),
			NULL,
			NULL,
			(GClassInitFunc) node_retval_class_init,
			NULL,
			NULL,
			sizeof (NodeRetval),
			0,
			(GInstanceInitFunc) node_retval_init
		};
		node_retval_type = g_type_register_static(GTK_TYPE_VBOX, "NodeRetval", &node_retval_info, 0);
	}
	return node_retval_type;
}

GtkWidget *
node_retval_new(void)
{
	return GTK_WIDGET(g_object_new(node_retval_get_type(), NULL));
}

void
node_retval_edit(GtkWidget *w, iks *x)
{
	NodeRetval *obj = (NodeRetval *) w;

	obj->x = x;

	gtk_combo_box_set_active(GTK_COMBO_BOX(obj->combo), 0);
	gtk_combo_box_set_active(GTK_COMBO_BOX(obj->rw_combo), 0);

	if (iks_strcmp(iks_name(x), "method") == 0) {
		gtk_widget_hide(obj->rw_combo);
		gtk_widget_hide(obj->rw_label);
	} else {
		gtk_widget_show(obj->rw_combo);
		gtk_widget_show(obj->rw_label);
	}
}

struct OMNodeEditor *
node_retval_get_editor(void)
{
	struct OMNodeEditor *ed;

	ed = g_malloc0(sizeof(struct OMNodeEditor));
	ed->w = node_retval_new();
	ed->expand = FALSE;
	ed->types = 1 << OM_METHOD | 1 << OM_PROPERTY;
	ed->edit_func = node_retval_edit;

	return ed;
}
