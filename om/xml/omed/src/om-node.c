/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - om-node.c
** widget for editing an om node
*/

#include "common.h"
#include "om-node.h"
#include "node-desc.h"
#include "node-acl.h"
#include "node-param.h"
#include "node-oper.h"
#include "node-retval.h"

static void
om_node_class_init(OMNodeClass *class)
{
}

static void
add_editor(OMNode *obj, struct OMNodeEditor *ed)
{
	ed->next = obj->editors;
	obj->editors = ed;
	gtk_box_pack_start(GTK_BOX(obj->edit_area), ed->w, ed->expand, ed->expand, 0);
}

static void
om_node_init(OMNode *obj)
{
	GtkWidget *hb;

	hb = gtk_hbox_new(FALSE, 3);
	gtk_widget_show(hb);
	gtk_box_pack_start(GTK_BOX(obj), hb, FALSE, TRUE, 0);

	// icon and name
	obj->icon = gtk_image_new();
	gtk_widget_show(obj->icon);
	gtk_box_pack_start(GTK_BOX(hb), obj->icon, FALSE, TRUE, 0);

	obj->name = gtk_entry_new();
	gtk_entry_set_editable(GTK_ENTRY(obj->name), FALSE);
	gtk_widget_show(obj->name);
	gtk_box_pack_start(GTK_BOX(hb), obj->name, TRUE, TRUE, 0);

	// edit area
	obj->edit_area = gtk_vbox_new(FALSE, 3);
	gtk_widget_show(obj->edit_area);
	gtk_box_pack_start(GTK_BOX(obj), obj->edit_area, TRUE, TRUE, 0);

	add_editor(obj, node_desc_get_editor());
	add_editor(obj, node_retval_get_editor());
	add_editor(obj, node_param_get_editor());
	add_editor(obj, node_oper_get_editor());
	add_editor(obj, node_acl_get_editor());
}

GType
om_node_get_type(void)
{
	static GType om_node_type = 0;

	if (!om_node_type) {
		static const GTypeInfo om_node_info = {
			sizeof (OMNodeClass),
			NULL,
			NULL,
			(GClassInitFunc) om_node_class_init,
			NULL,
			NULL,
			sizeof (OMNode),
			0,
			(GInstanceInitFunc) om_node_init
		};
		om_node_type = g_type_register_static(GTK_TYPE_VBOX, "OMNode", &om_node_info, 0);
	}
	return om_node_type;
}

GtkWidget *
om_node_new(void)
{
	return GTK_WIDGET(g_object_new(om_node_get_type(), NULL));
}

void
om_node_edit(OMNode *obj, const char *name, int type, iks *x)
{
	struct OMNodeEditor *ed;

	gtk_image_set_from_stock(GTK_IMAGE(obj->icon),
		om_stock_id(type),
		GTK_ICON_SIZE_BUTTON
	);
	gtk_entry_set_text(GTK_ENTRY(obj->name), name);

	for (ed = obj->editors; ed; ed = ed->next) {
		if ((1 << type) & ed->types) {
			gtk_widget_show(ed->w);
			if (ed->edit_func) ed->edit_func(ed->w, x);
		} else {
			gtk_widget_hide(ed->w);
			if (ed->edit_func) ed->edit_func(ed->w, NULL);
		}
	}
}

void
om_node_stop_editing(OMNode *obj)
{
	struct OMNodeEditor *ed;

	for (ed = obj->editors; ed; ed = ed->next) {
		if (ed->edit_func) ed->edit_func(ed->w, NULL);
	}
}
