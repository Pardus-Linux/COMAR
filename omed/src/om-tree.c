/*
** Copyright (c) 2004, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - om-tree.c
** widget for editing the om tree
*/

#include "common.h"
#include "om-tree.h"

enum {
	SELECT_SIGNAL,
	NR_SIGS
};

enum {
	COL_NODE,
	COL_NAME,
	COL_TYPE,
	NR_COLS
};

static guint om_tree_sigs[NR_SIGS] = { 0 };

static void
om_tree_class_init(OMTreeClass *class)
{
	om_tree_sigs[SELECT_SIGNAL] =
		g_signal_new ("om-tree-select", OM_TYPE_TREE,
			G_SIGNAL_RUN_FIRST, G_STRUCT_OFFSET (OMTreeClass, om_tree_select),
			NULL, NULL,
			g_cclosure_marshal_VOID__POINTER,
			G_TYPE_NONE, 1, G_TYPE_POINTER);
	class->om_tree_select = NULL;
}

static void
cb_render_icon(GtkTreeViewColumn *col, GtkCellRenderer *cell, GtkTreeModel *model, GtkTreeIter *iter, gpointer data)
{
	int type;

	gtk_tree_model_get(model, iter, COL_TYPE, &type, -1);
	g_object_set(cell, "stock-id", om_stock_id(type), NULL);
}

static void
cb_render_name(GtkTreeViewColumn *col, GtkCellRenderer *cell, GtkTreeModel *model, GtkTreeIter *iter, gpointer data)
{
	char *name;

	gtk_tree_model_get(model, iter, COL_NAME, &name, -1);
	g_object_set(cell, "text", name, NULL);
}

static void
cb_change_name(GtkCellRenderer *cell, const char *path, const char *new_name, OMTree *obj)
{
	GtkTreeIter iter;
	iks *x, *y;

	if (gtk_tree_model_get_iter_from_string(GTK_TREE_MODEL(obj->t_store), &iter, path) == TRUE) {
		gtk_tree_model_get(GTK_TREE_MODEL(obj->t_store), &iter, COL_NODE, &x, -1);
		y = iks_insert_attrib(x, "name", new_name);
		gtk_tree_store_set(obj->t_store, &iter, COL_NAME, iks_cdata(y), -1);
	}
}

static char *
make_name (OMTree *obj, GtkTreeIter *iter)
{
	GtkTreeIter iter1 = *iter, iter2;
	char *t1 = NULL;
	char *t2, *name;
	int type;

	while (1) {
		gtk_tree_model_get(GTK_TREE_MODEL(obj->t_store),
			&iter1,
			COL_TYPE, &type,
			COL_NAME, &name,
			-1
		);
		switch (type) {
			case OM_NAMESPACE:
				if (t1)
					t2 = g_strdup_printf("%s:%s", name, t1);
				else
					t2 = g_strdup(name);
				break;
			default:
				if (t1)
					t2 = g_strdup_printf("%s.%s", name, t1);
				else
					t2 = g_strdup(name);
				break;
		}
		if (t1) g_free (t1);
		t1 = t2;
		if (type == OM_NAMESPACE) break;
		gtk_tree_model_iter_parent(GTK_TREE_MODEL(obj->t_store), &iter2, &iter1);
		iter1 = iter2;
	}
	return t1;
}

static void
cb_update(GtkTreeSelection *sel, gpointer data)
{
	OMTree *obj = (OMTree *) data;
	struct OMTreeSelectSig ssig;
	GtkTreeModel *model;
	GtkTreeIter iter;

	if (gtk_tree_selection_get_selected(sel, &model, &iter) == FALSE)
		return;

	gtk_tree_model_get(model, &iter,
		COL_NODE, &ssig.x,
		COL_TYPE, &ssig.type,
		-1
	);
	ssig.name = make_name(obj, &iter);
	g_signal_emit(G_OBJECT(obj), om_tree_sigs[SELECT_SIGNAL], 0, &ssig);
	g_free(ssig.name);
}

static void
om_tree_init(OMTree *obj)
{
	GtkCellRenderer *cell;

	// model and view widget
	obj->t_store = gtk_tree_store_new(NR_COLS, G_TYPE_POINTER, G_TYPE_POINTER, G_TYPE_INT);
	gtk_tree_view_set_model(GTK_TREE_VIEW(obj), GTK_TREE_MODEL(obj->t_store));
	gtk_tree_view_set_headers_visible(GTK_TREE_VIEW(obj), FALSE);
	gtk_widget_set_size_request(GTK_WIDGET(obj), 160, -1);
	obj->t_select = gtk_tree_view_get_selection(GTK_TREE_VIEW(obj));
	gtk_tree_view_set_reorderable(GTK_TREE_VIEW(obj), TRUE);
	// columns
	obj->t_col = gtk_tree_view_column_new();
	gtk_tree_view_append_column(GTK_TREE_VIEW(obj), obj->t_col);
	// icon cell
	cell = gtk_cell_renderer_pixbuf_new();
	gtk_tree_view_column_pack_start(obj->t_col, cell, FALSE);
	gtk_tree_view_column_set_cell_data_func(obj->t_col, cell, cb_render_icon, NULL, NULL);
	// name cell
	cell = gtk_cell_renderer_text_new();
	obj->t_cell = cell;
	g_object_set(G_OBJECT(cell), "editable", TRUE, "editable-set", TRUE, NULL);
	g_signal_connect(G_OBJECT(cell), "edited", G_CALLBACK(cb_change_name), obj);
	gtk_tree_view_column_pack_start(obj->t_col, cell, TRUE);
	gtk_tree_view_column_set_cell_data_func(obj->t_col, cell, cb_render_name, NULL, NULL);
	// signals
	g_signal_connect(G_OBJECT(obj->t_select), "changed", G_CALLBACK(cb_update), obj);
}

GType
om_tree_get_type(void)
{
	static GType om_tree_type = 0;

	if (!om_tree_type) {
		static const GTypeInfo om_tree_info = {
			sizeof (OMTreeClass),
			NULL,
			NULL,
			(GClassInitFunc) om_tree_class_init,
			NULL,
			NULL,
			sizeof (OMTree),
			0,
			(GInstanceInitFunc) om_tree_init
		};
		om_tree_type = g_type_register_static(GTK_TYPE_TREE_VIEW, "OMTree", &om_tree_info, 0);
	}
	return om_tree_type;
}

GtkWidget *
om_tree_new(void)
{
	return GTK_WIDGET(g_object_new(om_tree_get_type(), NULL));
}

static void
add_nodes(OMTree *obj, GtkTreeIter *parent, iks *node)
{
	GtkTreeIter iter;
	iks *x, *y;
	char *t, *name;
	int type;

	// split node and its information from child nodes
	x = iks_copy(node);
	for (y = iks_child(x); y; y = iks_next(y)) {
		if (iks_type(y) == IKS_TAG) {
			t = iks_name(y);
			if (iks_strcmp(t, "object") == 0
				|| iks_strcmp(t, "method") == 0
				|| iks_strcmp(t, "property") == 0) {
					iks_hide(y);
			}
		} else {
			// also remove unnecessary whitespace
			iks_hide(y);
		}
	}
	y = iks_copy(x);
	iks_delete(x);
	// append to the tree
	name = iks_find_attrib(y, "name");
	type = om_type(iks_name(y));
	gtk_tree_store_append(obj->t_store, &iter, parent);
	gtk_tree_store_set (obj->t_store, &iter,
		COL_NODE, y,
		COL_NAME, name,
		COL_TYPE, type,
		-1
	);
	// recurse for child nodes
	for (y = iks_first_tag(node); y; y = iks_next_tag(y)) {
		t = iks_name(y);
		if (iks_strcmp(t, "object") == 0
			|| iks_strcmp(t, "method") == 0
			|| iks_strcmp(t, "property") == 0) {
				add_nodes(obj, &iter, y);
		}
	}
}

int
om_tree_set(OMTree *obj, iks *om)
{
	iks *ns;

	if (iks_strcmp(iks_name(om), "comar-om") != 0) return -1;

	ns = iks_find(om, "namespace");
	add_nodes(obj, NULL, ns);

	return 0;
}

static void
get_nodes(OMTree *obj, GtkTreeIter *parent, iks *x)
{
	GtkTreeModel *model;
	GtkTreeIter iter;
	gboolean go;
	iks *y, *z;

	model = GTK_TREE_MODEL(obj->t_store);
	go = gtk_tree_model_iter_children(model, &iter, parent);
	while (go) {
		gtk_tree_model_get(model, &iter, COL_NODE, &y, -1);
		z = iks_copy_within(y, iks_stack(x));
		z = iks_insert_node(x, z);
		iks_insert_cdata(z, "\n", 1);
		if (gtk_tree_model_iter_has_child(model, &iter)) {
			get_nodes(obj, &iter, z);
			iks_insert_cdata(z, "\n", 1);
		}
		iks_insert_cdata(x, "\n", 1);
		go = gtk_tree_model_iter_next(model, &iter);
	}
	iks_insert_cdata(x, "\n", 1);
}

iks *
om_tree_get(OMTree *obj)
{
	GtkTreeIter iter;
	iks *om;

	om = iks_new("comar-om");
	iks_insert_cdata(om, "\n", 1);
	gtk_tree_model_get_iter_first(GTK_TREE_MODEL(obj->t_store), &iter);
	get_nodes(obj, NULL, om);
	return om;
}

iks *
om_tree_get_current(OMTree *obj)
{
	GtkTreeModel *model;
	GtkTreeIter iter;
	iks *x, *y;

	if (gtk_tree_selection_get_selected(obj->t_select, &model, &iter) == FALSE)
		return NULL;

	gtk_tree_model_get(model, &iter, COL_NODE, &x, -1);
	y = iks_copy(x);
	get_nodes(obj, &iter, y);
	return y;
}

static gboolean
cb_remove_func(GtkTreeModel *model, GtkTreePath *path, GtkTreeIter *iter, gpointer data)
{
	iks *x;

	gtk_tree_model_get(model, iter, COL_NODE, &x, -1);
	iks_delete(x);
	return FALSE;
}

void
om_tree_clear(OMTree *obj)
{
	gtk_tree_model_foreach(GTK_TREE_MODEL(obj->t_store), cb_remove_func, obj);
	gtk_tree_store_clear (obj->t_store);
}

void
om_tree_add(OMTree *obj, int type, const char *name)
{
	GtkTreeIter parent, iter;
	GtkTreeModel *model;
	GtkTreePath *path;
	int ptype;
	iks *x, *y;

	if (FALSE == gtk_tree_selection_get_selected(obj->t_select, &model, &parent)
		&& type != OM_NAMESPACE) return;

	// if item isnt an object, append child to the item's parent
	if (type != OM_NAMESPACE) {
		gtk_tree_model_get(model, &parent, COL_TYPE, &ptype, -1);
		if (ptype != OM_OBJECT && ptype != OM_NAMESPACE) {
			iter = parent;
			gtk_tree_model_iter_parent(model, &parent, &iter);
		}
	}

	// append new node
	x = iks_new(om_name(type));
	y = iks_insert_attrib(x, "name", name);
	if (OM_NAMESPACE == type) {
		gtk_tree_store_append(obj->t_store, &iter, NULL);
	} else {
		gtk_tree_store_append(obj->t_store, &iter, &parent);
	}
	gtk_tree_store_set(obj->t_store, &iter,
		COL_NODE, x,
		COL_TYPE, type,
		COL_NAME, iks_cdata(y),
		-1
	);

	if (type != OM_NAMESPACE) {
		// expand parent
		path = gtk_tree_model_get_path(model, &parent);
		gtk_tree_view_expand_row(GTK_TREE_VIEW(obj), path, FALSE);
		gtk_tree_path_free(path);
		// start editing
		path = gtk_tree_model_get_path(model, &iter);
		gtk_tree_selection_select_path(obj->t_select, path);
		if (!obj->t_col->editable_widget)
			gtk_tree_view_set_cursor(GTK_TREE_VIEW(obj), path, obj->t_col, TRUE);
		gtk_widget_grab_focus(GTK_WIDGET(obj));
		gtk_tree_path_free(path);
	}
}

void
om_tree_remove(OMTree *obj)
{
	GtkTreeModel *model;
	GtkTreeIter iter;
	iks *x;
	int type;

	if (FALSE == gtk_tree_selection_get_selected(obj->t_select, &model, &iter))
		return;

	gtk_tree_model_get(model, &iter, COL_NODE, &x, COL_TYPE, &type, -1);
	if (OM_NAMESPACE == type) return;

	// FIXME: dont forget to remove sub nodes
	iks_delete(x);
	gtk_tree_store_remove(obj->t_store, &iter);
}

gchar *
om_stock_id(int type)
{
	switch (type) {
		case OM_NAMESPACE: return GTK_STOCK_HOME;
		case OM_OBJECT: return GTK_STOCK_SELECT_COLOR;
		case OM_METHOD: return GTK_STOCK_CONVERT;
		case OM_PROPERTY: return GTK_STOCK_PREFERENCES;
		default: return "";
	}
}

int
om_type(const char *name)
{
	if (!name) return OM_UNKNOWN;
	if (strcmp(name, "namespace") == 0) return OM_NAMESPACE;
	if (strcmp(name, "object") == 0) return OM_OBJECT;
	if (strcmp(name, "method") == 0) return OM_METHOD;
	if (strcmp(name, "property") == 0) return OM_PROPERTY;
	return OM_UNKNOWN;
}

char *
om_name(int type)
{
	switch (type) {
		case OM_NAMESPACE: return "namespace";
		case OM_OBJECT: return "object";
		case OM_METHOD: return "method";
		case OM_PROPERTY: return "property";
		default: return "";
	}
}
