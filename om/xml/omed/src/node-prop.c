/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - node-prop.c
** property attributes widget
*/

#include "common.h"
#include "node-prop.h"

static void
node_prop_class_init(NodePropClass *class)
{
}

static void
node_prop_init(NodeProp *obj)
{
	GtkWidget *hb, *b;

	hb = gtk_hbox_new(FALSE, 6);
	gtk_widget_show(hb);
	gtk_box_pack_start(GTK_BOX(obj), hb, FALSE, FALSE, 0);

	b = gtk_label_new(_("Access type:"));
	gtk_widget_show(b);
	gtk_box_pack_start(GTK_BOX(hb), b, FALSE, FALSE, 0);

	obj->combo = gtk_combo_box_new_text();
	gtk_combo_box_append_text(GTK_COMBO_BOX(obj->combo), _("Read/Write"));
	gtk_combo_box_append_text(GTK_COMBO_BOX(obj->combo), _("Read only"));
	gtk_combo_box_append_text(GTK_COMBO_BOX(obj->combo), _("Write only"));
	gtk_widget_show(obj->combo);
	gtk_box_pack_start(GTK_BOX(hb), obj->combo, FALSE, FALSE, 0);

	obj->loc = gtk_check_button_new_with_label(_("Localized"));
	gtk_widget_show(obj->loc);
	gtk_box_pack_start(GTK_BOX(hb), obj->loc, FALSE, FALSE, 0);

	b = gtk_label_new("");
	gtk_widget_show(b);
	gtk_box_pack_start(GTK_BOX(hb), b, TRUE, FALSE, 0);

}

GType
node_prop_get_type(void)
{
	static GType node_prop_type = 0;

	if (!node_prop_type) {
		static const GTypeInfo node_prop_info = {
			sizeof (NodePropClass),
			NULL,
			NULL,
			(GClassInitFunc) node_prop_class_init,
			NULL,
			NULL,
			sizeof (NodeProp),
			0,
			(GInstanceInitFunc) node_prop_init
		};
		node_prop_type = g_type_register_static(GTK_TYPE_VBOX, "NodeProp", &node_prop_info, 0);
	}
	return node_prop_type;
}

GtkWidget *
node_prop_new(void)
{
	return GTK_WIDGET(g_object_new(node_prop_get_type(), NULL));
}

void
node_prop_edit(GtkWidget *w, iks *x)
{
	NodeProp *obj = (NodeProp *) w;

	obj->x = x;

	gtk_combo_box_set_active(GTK_COMBO_BOX(obj->combo), 0);
}
