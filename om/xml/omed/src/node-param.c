/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - node-param.c
** method parameters widget
*/

#include "common.h"
#include "node-param.h"

static void
node_param_class_init(NodeParamClass *class)
{
}

static void
cb_add(NodeParam *obj)
{
	GtkTreeIter iter;
	iks *x;

	if (NULL == obj->x) return;

	x = iks_insert(obj->inputs, "parameter");
	iks_insert_attrib(x, "name", "(new)");
	gtk_list_store_append(obj->t_store, &iter);
	gtk_list_store_set(obj->t_store, &iter, 0, x, -1);
}

static void
cb_remove(NodeParam *obj)
{
	GtkTreeModel *model;
	GtkTreeIter iter;
	iks *x;

	if (FALSE == gtk_tree_selection_get_selected(obj->t_select, &model, &iter))
		return;

	gtk_tree_model_get(model, &iter, 0, &x, -1);
	iks_hide(x);

	gtk_list_store_remove(obj->t_store, &iter);
}

static void
cb_change_name(GtkCellRenderer *cell, const char *path, const char *new_name, NodeParam *obj)
{
	GtkTreeIter iter;
	iks *x;

	if (gtk_tree_model_get_iter_from_string(GTK_TREE_MODEL(obj->t_store), &iter, path) == TRUE) {
		gtk_tree_model_get(GTK_TREE_MODEL(obj->t_store), &iter, 0, &x, -1);
		iks_insert_attrib(x, "name", new_name);
	}
}

static void
cb_render(GtkTreeViewColumn *col, GtkCellRenderer *cell, GtkTreeModel *model, GtkTreeIter *iter, gpointer data)
{
	iks *x;

	gtk_tree_model_get(model, iter, 0, &x, -1);
	g_object_set(cell, "text", iks_find_attrib(x, "name"), NULL);
}

static void
node_param_init(NodeParam *obj)
{
	GtkWidget *lab, *hb, *sw, *vb, *hb2, *b;
	GtkTreeViewColumn *col;
	GtkCellRenderer *cell;

	obj->x = NULL;

	// label
	lab = gtk_label_new(_("Parameters:"));
	gtk_misc_set_alignment(GTK_MISC(lab), 0, 0);
	gtk_widget_show(lab);
	gtk_box_pack_start(GTK_BOX(obj), lab, FALSE, TRUE, 0);

	hb = gtk_hbox_new(FALSE, 0);
	gtk_widget_show(hb);
	gtk_box_pack_start(GTK_BOX(obj), hb, TRUE, TRUE, 0);

	// list area
	vb = gtk_vbox_new(FALSE, 0);
	gtk_widget_show(vb);
	gtk_box_pack_start(GTK_BOX(hb), vb, TRUE, TRUE, 0);

	sw = gtk_scrolled_window_new(NULL, NULL);
	gtk_widget_show(sw);
	gtk_scrolled_window_set_shadow_type(GTK_SCROLLED_WINDOW(sw), GTK_SHADOW_ETCHED_IN);
	gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(sw), GTK_POLICY_AUTOMATIC, GTK_POLICY_ALWAYS);
	gtk_box_pack_start(GTK_BOX(vb), sw, TRUE, TRUE, 0);

	// parameter list
	obj->t_store = gtk_list_store_new(1, G_TYPE_POINTER);
	obj->t_view = gtk_tree_view_new_with_model(GTK_TREE_MODEL(obj->t_store));
	obj->t_select = gtk_tree_view_get_selection(GTK_TREE_VIEW (obj->t_view));
	gtk_widget_show(obj->t_view);
	//gtk_tree_view_set_reorderable (GTK_TREE_VIEW (tree_view), TRUE);

	col = gtk_tree_view_column_new();
	gtk_tree_view_append_column(GTK_TREE_VIEW(obj->t_view), col);
	cell = gtk_cell_renderer_text_new();
	g_object_set(G_OBJECT(cell), "editable", TRUE, "editable-set", TRUE, NULL);
	g_signal_connect(G_OBJECT(cell), "edited", G_CALLBACK(cb_change_name), obj);
	gtk_tree_view_column_pack_start(col, cell, TRUE);
	gtk_tree_view_column_set_cell_data_func(col, cell, cb_render, NULL, NULL);
//	g_signal_connect (G_OBJECT (tree_select), "changed", G_CALLBACK (cb_update), NULL);
	gtk_container_add(GTK_CONTAINER(sw), obj->t_view);

	// buttons
	hb2 = gtk_hbox_new(TRUE, 3);
	gtk_widget_show(hb2);
	gtk_container_set_border_width(GTK_CONTAINER(hb2), 1);
	gtk_box_pack_start(GTK_BOX(vb), hb2, FALSE, TRUE, 0);

	b = pix_button(GTK_STOCK_ADD, _("Add Parameter"));
	gtk_container_add(GTK_CONTAINER(hb2), b);
	g_signal_connect_swapped(G_OBJECT(b), "clicked", G_CALLBACK(cb_add), obj);

	b = pix_button(GTK_STOCK_REMOVE, _("Remove"));
	gtk_container_add(GTK_CONTAINER(hb2), b);
	g_signal_connect_swapped(G_OBJECT(b), "clicked", G_CALLBACK(cb_remove), obj);

	b = gtk_label_new("details...");
	gtk_widget_show(b);
	gtk_box_pack_start(GTK_BOX(hb), b, TRUE, TRUE, 0);
}

GType
node_param_get_type(void)
{
	static GType node_param_type = 0;

	if (!node_param_type) {
		static const GTypeInfo node_param_info = {
			sizeof (NodeParamClass),
			NULL,
			NULL,
			(GClassInitFunc) node_param_class_init,
			NULL,
			NULL,
			sizeof (NodeParam),
			0,
			(GInstanceInitFunc) node_param_init
		};
		node_param_type = g_type_register_static(GTK_TYPE_VBOX, "NodeParam", &node_param_info, 0);
	}
	return node_param_type;
}

GtkWidget *
node_param_new(void)
{
	return GTK_WIDGET(g_object_new(node_param_get_type(), NULL));
}

void
node_param_edit(GtkWidget *w, iks *x)
{
	NodeParam *obj = NODE_PARAM(w);
	GtkTreeIter iter;
	iks *y;

	obj->x = x;
	gtk_list_store_clear(obj->t_store);
	if (x) {
		obj->inputs = iks_find(x, "inputs");
		if (obj->inputs) {
			for (y = iks_first_tag(obj->inputs); y; y = iks_next_tag(y)) {
				if (iks_strcmp(iks_name(y), "parameter") == 0) {
					gtk_list_store_append(obj->t_store, &iter);
					gtk_list_store_set(obj->t_store, &iter, 0, y, -1);
				}
			}
		} else {
			obj->inputs = iks_insert(x, "inputs");
		}
	}
}

struct OMNodeEditor *
node_param_get_editor(void)
{
	struct OMNodeEditor *ed;

	ed = g_malloc0(sizeof(struct OMNodeEditor));
	ed->w = node_param_new();
	ed->expand = TRUE;
	ed->types = 1 << OM_METHOD;
	ed->edit_func = node_param_edit;

	return ed;
}
