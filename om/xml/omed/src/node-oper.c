/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - node-oper.c
** node operating mode widget
*/

#include "common.h"
#include "node-oper.h"

static void
node_oper_class_init(NodeOperClass *class)
{
}

static void
node_oper_init(NodeOper *obj)
{
	GtkWidget *hb, *b;

	hb = gtk_hbox_new(FALSE, 6);
	gtk_widget_show(hb);
	gtk_box_pack_start(GTK_BOX(obj), hb, FALSE, FALSE, 0);

	b = gtk_label_new(_("Operating selection:"));
	gtk_widget_show(b);
	gtk_box_pack_start(GTK_BOX(hb), b, FALSE, FALSE, 0);

	obj->sel_combo = gtk_combo_box_new_text();
	gtk_combo_box_append_text(GTK_COMBO_BOX(obj->sel_combo), _("Best match"));
	gtk_combo_box_append_text(GTK_COMBO_BOX(obj->sel_combo), _("All"));
	gtk_widget_show(obj->sel_combo);
	gtk_box_pack_start(GTK_BOX(hb), obj->sel_combo, FALSE, FALSE, 0);

	b = gtk_label_new(_("advance:"));
	gtk_widget_show(b);
	gtk_box_pack_start(GTK_BOX(hb), b, FALSE, FALSE, 0);

	obj->adv_combo = gtk_combo_box_new_text();
	gtk_combo_box_append_text(GTK_COMBO_BOX(obj->adv_combo), _("First match"));
	gtk_combo_box_append_text(GTK_COMBO_BOX(obj->adv_combo), _("Collect"));
	gtk_combo_box_append_text(GTK_COMBO_BOX(obj->adv_combo), _("All"));
	gtk_widget_show(obj->adv_combo);
	gtk_box_pack_start(GTK_BOX(hb), obj->adv_combo, FALSE, FALSE, 0);

	b = gtk_label_new("");
	gtk_widget_show(b);
	gtk_box_pack_start(GTK_BOX(hb), b, TRUE, FALSE, 0);

}

GType
node_oper_get_type(void)
{
	static GType node_oper_type = 0;

	if (!node_oper_type) {
		static const GTypeInfo node_oper_info = {
			sizeof (NodeOperClass),
			NULL,
			NULL,
			(GClassInitFunc) node_oper_class_init,
			NULL,
			NULL,
			sizeof (NodeOper),
			0,
			(GInstanceInitFunc) node_oper_init
		};
		node_oper_type = g_type_register_static(GTK_TYPE_VBOX, "NodeOper", &node_oper_info, 0);
	}
	return node_oper_type;
}

GtkWidget *
node_oper_new(void)
{
	return GTK_WIDGET(g_object_new(node_oper_get_type(), NULL));
}

void
node_oper_edit(GtkWidget *w, iks *x)
{
	NodeOper *obj = (NodeOper *) w;

	obj->x = x;

	gtk_combo_box_set_active(GTK_COMBO_BOX(obj->sel_combo), 0);
	gtk_combo_box_set_active(GTK_COMBO_BOX(obj->adv_combo), 0);

}
