/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - node-acl.c
** access control list editor widget
*/

#include "common.h"
#include "node-acl.h"

enum {
	COL_NODE,
	NR_COLS
};

static void
om_acl_class_init(OMAclClass *class)
{
}

static void
add_node(OMAcl *obj, iks *x)
{
	GtkTreeIter iter;

	if (NULL == obj->x) return;

	if (NULL == x) {
		x = iks_insert(obj->acl, "rule");
		iks_insert_cdata(iks_insert(x, "chain"), "User", 0);
		iks_insert_cdata(iks_insert(x, "policy"), "Allow", 0);
	}
	gtk_list_store_append (obj->t_store, &iter);
	gtk_list_store_set (obj->t_store, &iter, COL_NODE, x, -1);
}

static void
cb_add(OMAcl *obj)
{
	add_node(obj, NULL);
}

static void
cb_remove(OMAcl *obj)
{
	GtkTreeModel *model;
	GtkTreeIter iter;
	iks *x;

	if (FALSE == gtk_tree_selection_get_selected (obj->t_select, &model, &iter)) return;
	gtk_tree_model_get(model, &iter, COL_NODE, &x, -1);
	iks_hide(x);
	gtk_list_store_remove (obj->t_store, &iter);
}

static void
cb_render_quick(GtkTreeViewColumn *col, GtkCellRenderer *cell, GtkTreeModel *model, GtkTreeIter *iter, gpointer data)
{
	iks *x;
	gboolean act = FALSE;

	gtk_tree_model_get(model, iter, COL_NODE, &x, -1);
	if (iks_find(x, "quick")) act = TRUE;
	g_object_set(cell, "active", act, NULL);
}

static void
cb_quick(GtkCellRendererToggle *tog, gchar *path, OMAcl *obj)
{
	GtkTreeIter iter;
	iks *x, *y;

	if (gtk_tree_model_get_iter_from_string(GTK_TREE_MODEL(obj->t_store), &iter, path) == TRUE) {
		gtk_tree_model_get(GTK_TREE_MODEL(obj->t_store), &iter, COL_NODE, &x, -1);
		y = iks_find(x, "quick");
		if (y) iks_hide(y);
		else iks_insert(x, "quick");
	}
}

static void
cb_render_policy(GtkTreeViewColumn *col, GtkCellRenderer *cell, GtkTreeModel *model, GtkTreeIter *iter, gpointer data)
{
	iks *x;

	gtk_tree_model_get(model, iter, COL_NODE, &x, -1);
	g_object_set(cell, "text", iks_find_cdata(x, "policy"), NULL);
}

static void
cb_policy(GtkCellRenderer *cell, const char *path, const char *new_val, OMAcl *obj)
{
	GtkTreeIter iter;
	iks *x, *y;

	if(gtk_tree_model_get_iter_from_string(GTK_TREE_MODEL(obj->t_store), &iter, path) == TRUE) {
		gtk_tree_model_get(GTK_TREE_MODEL(obj->t_store), &iter, COL_NODE, &x, -1);
		y = iks_find(x, "policy");
		if (!y) y = iks_insert(x, "policy");
		if (iks_strcmp(iks_cdata(iks_child(y)), new_val) != 0) {
			iks_hide(iks_child(y));
			iks_insert_cdata(y, new_val, 0);
		}
	}
}

static void
cb_render_not(GtkTreeViewColumn *col, GtkCellRenderer *cell, GtkTreeModel *model, GtkTreeIter *iter, gpointer data)
{
	iks *x;
	gboolean act = FALSE;

	gtk_tree_model_get(model, iter, COL_NODE, &x, -1);
	if (iks_find(x, "not")) act = TRUE;
	g_object_set(cell, "active", act, NULL);
}

static void
cb_not(GtkCellRendererToggle *tog, gchar *path, OMAcl *obj)
{
	GtkTreeIter iter;
	iks *x, *y;

	if (gtk_tree_model_get_iter_from_string(GTK_TREE_MODEL(obj->t_store), &iter, path) == TRUE) {
		gtk_tree_model_get(GTK_TREE_MODEL(obj->t_store), &iter, COL_NODE, &x, -1);
		y = iks_find(x, "not");
		if (y) iks_hide(y);
		else iks_insert(x, "not");
	}
}

static void
cb_render_chain(GtkTreeViewColumn *col, GtkCellRenderer *cell, GtkTreeModel *model, GtkTreeIter *iter, gpointer data)
{
	iks *x;

	gtk_tree_model_get(model, iter, COL_NODE, &x, -1);
	g_object_set(cell, "text", iks_find_cdata(x, "chain"), NULL);
}

static void
cb_chain(GtkCellRenderer *cell, const char *path, const char *new_val, OMAcl *obj)
{
	GtkTreeIter iter;
	iks *x, *y;

	if(gtk_tree_model_get_iter_from_string(GTK_TREE_MODEL(obj->t_store), &iter, path) == TRUE) {
		gtk_tree_model_get(GTK_TREE_MODEL(obj->t_store), &iter, COL_NODE, &x, -1);
		y = iks_find(x, "chain");
		if (!y) y = iks_insert(x, "chain");
		if (iks_strcmp(iks_cdata(iks_child(y)), new_val) != 0) {
			iks_hide(iks_child(y));
			iks_insert_cdata(y, new_val, 0);
		}
	}
}

static void
cb_render_value(GtkTreeViewColumn *col, GtkCellRenderer *cell, GtkTreeModel *model, GtkTreeIter *iter, gpointer data)
{
	iks *x;

	gtk_tree_model_get(model, iter, COL_NODE, &x, -1);
	g_object_set(cell, "text", iks_find_cdata(x, "value"), NULL);
}

static void
cb_value(GtkCellRenderer *cell, const char *path, const char *new_val, OMAcl *obj)
{
	GtkTreeIter iter;
	iks *x, *y;

	if(gtk_tree_model_get_iter_from_string(GTK_TREE_MODEL(obj->t_store), &iter, path) == TRUE) {
		gtk_tree_model_get(GTK_TREE_MODEL(obj->t_store), &iter, COL_NODE, &x, -1);
		y = iks_find(x, "value");
		if (!y) y = iks_insert(x, "value");
		if (iks_strcmp(iks_cdata(iks_child(y)), new_val) != 0) {
			iks_hide(iks_child(y));
			iks_insert_cdata(y, new_val, 0);
		}
	}
}

static void
cb_inherit(GtkComboBox *combo, OMAcl *obj)
{
	int act;
	iks *x;

	act = gtk_combo_box_get_active(combo);
	x = iks_find(obj->acl, "standalone");
	if (act == 0) {
		if (x) iks_hide(x);
	} else {
		if (!x) iks_insert(obj->acl, "standalone");
	}
}

static void
om_acl_init(OMAcl *obj)
{
	GtkWidget *hb, *b, *sw;
	GtkCellRenderer *cell;
	GtkTreeViewColumn *col;

	// inheritance group
	hb = gtk_hbox_new(FALSE, 6);
	obj->inherit_box = hb;
	gtk_widget_show(hb);
	gtk_box_pack_start(GTK_BOX(obj), hb, FALSE, FALSE, 0);

	b = gtk_label_new(_("Access rights"));
	gtk_widget_show(b);
	gtk_box_pack_start(GTK_BOX(hb), b, FALSE, FALSE, 0);

	obj->inherit_combo = gtk_combo_box_new_text();
	gtk_combo_box_append_text(GTK_COMBO_BOX(obj->inherit_combo), _("Inherited from parent"));
	gtk_combo_box_append_text(GTK_COMBO_BOX(obj->inherit_combo), _("Standalone"));
	gtk_widget_show(obj->inherit_combo);
	g_signal_connect(G_OBJECT(obj->inherit_combo), "changed", G_CALLBACK(cb_inherit), obj);
	gtk_box_pack_start(GTK_BOX(hb), obj->inherit_combo, FALSE, FALSE, 0);

	b = gtk_label_new("");
	gtk_widget_show(b);
	gtk_box_pack_start(GTK_BOX(hb), b, TRUE, FALSE, 0);

	// global label
	obj->label = gtk_label_new(_("Global access rights"));
	gtk_box_pack_start(GTK_BOX(obj), obj->label, FALSE, FALSE, 0);

	// rule chains
	sw = gtk_scrolled_window_new(NULL, NULL);
	gtk_widget_show(sw);
	gtk_scrolled_window_set_shadow_type(GTK_SCROLLED_WINDOW(sw), GTK_SHADOW_ETCHED_IN);
	gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(sw), GTK_POLICY_AUTOMATIC, GTK_POLICY_ALWAYS);
	gtk_box_pack_start(GTK_BOX(obj), sw, TRUE, TRUE, 0);

	obj->t_store = gtk_list_store_new(
		NR_COLS,
		G_TYPE_POINTER
	);
	obj->t_view = gtk_tree_view_new_with_model(GTK_TREE_MODEL(obj->t_store));
	obj->t_select = gtk_tree_view_get_selection(GTK_TREE_VIEW(obj->t_view));
	gtk_tree_view_set_reorderable(GTK_TREE_VIEW(obj->t_view), TRUE);

	cell = gtk_cell_renderer_toggle_new();
	col = gtk_tree_view_column_new_with_attributes(_("Quick"), cell, NULL);
	gtk_tree_view_append_column(GTK_TREE_VIEW(obj->t_view), col);
	g_signal_connect(G_OBJECT(cell), "toggled", G_CALLBACK(cb_quick), obj);
	gtk_tree_view_column_set_cell_data_func(col, cell, cb_render_quick, NULL, NULL);

	cell = gtk_cell_combo(3, "Allow", "Read only", "Deny");
	g_object_set(G_OBJECT(cell), "editable", TRUE, NULL);
	col = gtk_tree_view_column_new_with_attributes(_("Policy"), cell, NULL);
	gtk_tree_view_append_column(GTK_TREE_VIEW(obj->t_view), col);
	g_signal_connect(G_OBJECT(cell), "edited", G_CALLBACK(cb_policy), obj);
	gtk_tree_view_column_set_cell_data_func(col, cell, cb_render_policy, NULL, NULL);

	cell = gtk_cell_renderer_toggle_new();
	col = gtk_tree_view_column_new_with_attributes(_("Not"), cell, NULL);
	gtk_tree_view_append_column(GTK_TREE_VIEW(obj->t_view), col);
	g_signal_connect(G_OBJECT(cell), "toggled", G_CALLBACK(cb_not), obj);
	gtk_tree_view_column_set_cell_data_func(col, cell, cb_render_not, NULL, NULL);

	cell = gtk_cell_combo(6,
		"User", "Realm", "Group",
		"Verified", "Crypted", "Caller"
	);
	g_object_set(G_OBJECT(cell), "editable", TRUE, NULL);
	col = gtk_tree_view_column_new_with_attributes (_("Chain"), cell, NULL);
	gtk_tree_view_append_column (GTK_TREE_VIEW (obj->t_view), col);
	g_signal_connect(G_OBJECT(cell), "edited", G_CALLBACK(cb_chain), obj);
	gtk_tree_view_column_set_cell_data_func(col, cell, cb_render_chain, NULL, NULL);

	cell = gtk_cell_renderer_text_new();
	g_object_set(G_OBJECT(cell), "editable", TRUE, NULL);
	col = gtk_tree_view_column_new_with_attributes(_("Value"), cell, NULL);
	gtk_tree_view_append_column(GTK_TREE_VIEW(obj->t_view), col);
	g_signal_connect(G_OBJECT(cell), "edited", G_CALLBACK(cb_value), obj);
	gtk_tree_view_column_set_cell_data_func(col, cell, cb_render_value, NULL, NULL);

	// buttons
	hb = gtk_hbutton_box_new();
	gtk_widget_show(hb);
	gtk_button_box_set_layout(GTK_BUTTON_BOX(hb), GTK_BUTTONBOX_START);
	gtk_box_pack_start(GTK_BOX(obj), hb, FALSE, TRUE, 0);

	b = gtk_button_new_from_stock(GTK_STOCK_ADD);
	gtk_widget_show(b);
	gtk_container_add(GTK_CONTAINER(hb), b);
	g_signal_connect_swapped(G_OBJECT(b), "clicked", G_CALLBACK(cb_add), obj);

	b = gtk_button_new_from_stock(GTK_STOCK_REMOVE);
	gtk_widget_show(b);
	gtk_container_add(GTK_CONTAINER(hb), b);
	g_signal_connect_swapped(G_OBJECT(b), "clicked", G_CALLBACK(cb_remove), obj);

	gtk_widget_show(obj->t_view);
	gtk_container_add(GTK_CONTAINER(sw), obj->t_view);
}

GType
om_acl_get_type(void)
{
	static GType om_acl_type = 0;

	if (!om_acl_type) {
		static const GTypeInfo om_acl_info = {
			sizeof (OMAclClass),
			NULL,
			NULL,
			(GClassInitFunc) om_acl_class_init,
			NULL,
			NULL,
			sizeof (OMAcl),
			0,
			(GInstanceInitFunc) om_acl_init
		};
		om_acl_type = g_type_register_static(GTK_TYPE_VBOX, "NodeAcl", &om_acl_info, 0);
	}
	return om_acl_type;
}

GtkWidget *
node_acl_new(void)
{
	return GTK_WIDGET(g_object_new(om_acl_get_type(), NULL));
}

void
node_acl_edit(GtkWidget *w, iks *x)
{
	OMAcl *obj = (OMAcl *) w;
	iks *y;

	gtk_list_store_clear(obj->t_store);
	obj->x = x;
	if (NULL == x) return;

	if (iks_strcmp(iks_name(x), "namespace") == 0) {
		gtk_widget_show(obj->label);
		gtk_widget_hide(obj->inherit_box);
	} else {
		gtk_widget_hide(obj->label);
		gtk_widget_show(obj->inherit_box);
	}

	obj->acl = iks_find(x, "acl");
	if (!obj->acl) obj->acl = iks_insert(x, "acl");

	if (iks_find(obj->acl, "standalone")) {
		gtk_combo_box_set_active(GTK_COMBO_BOX(obj->inherit_combo), 1);
	} else {
		gtk_combo_box_set_active(GTK_COMBO_BOX(obj->inherit_combo), 0);
	}

	for (y = iks_first_tag(obj->acl); y; y = iks_next_tag(y)) {
		if (iks_strcmp(iks_name(y), "rule") == 0) {
			add_node(obj,y);
		}
	}
}
