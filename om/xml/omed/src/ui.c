/*
** Copyright (c) 2004, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - ui.c
** main window ui
*/

#include "common.h"
#include "csl-edit.h"
#include "om-tree.h"
#include "om-node.h"

char *om_file_name;
gboolean om_changed;

enum {
	COL_NODE,
	NR_COLS
};

GtkWidget *main_window;
static GtkWidget *w_om_tree;
static GtkWidget *w_om_node;
static GtkWidget *status;
static guint status_id;

iks *
ui_serialize_om (void)
{
	return om_tree_get(OM_TREE(w_om_tree));
}

int
ui_load_om (iks *om)
{
	if (om_tree_set(OM_TREE(w_om_tree), om)) {
		message_box ("Not a COMAR OM file!");
		return 0;
	}
	return 1;
}

static void
cb_add_node (char *name)
{
	om_tree_add (OM_TREE(w_om_tree), OM_OBJECT, name);
}

static void
cb_add_method (char *name)
{
	om_tree_add (OM_TREE(w_om_tree), OM_METHOD, name);
}

static void
cb_add_property (char *name)
{
	om_tree_add (OM_TREE(w_om_tree), OM_PROPERTY, name);
}

static void
cb_remove_node (void)
{
	om_node_stop_editing(OM_NODE(w_om_node));
	om_tree_remove(OM_TREE(w_om_tree));
}

void
ui_clear_nodes (void)
{
	om_node_stop_editing(OM_NODE(w_om_node));
	om_tree_clear(OM_TREE(w_om_tree));
}

void
ui_open (char *file, gpointer data)
{
	iks *x;

	if (IKS_OK != iks_load (file, &x)) {
		message_box ("Cannot open OM file!");
		return;
	}

	ui_clear_nodes ();
	if (ui_load_om (x)) {
		if (om_file_name) g_free (om_file_name);
		om_file_name = g_strdup (file);
	}
	iks_delete (x);
}

void
ui_save (char *file, gpointer data)
{
	iks *x;
	int flag = 0;

	if (NULL == file) {
		flag = 1;
		file = om_file_name;
	}

	x = ui_serialize_om ();
	if (IKS_OK != iks_save (file, x)) {
		message_box ("Cannot save OM file!");
	} else {
		if (flag == 0) {
			if (om_file_name) g_free (om_file_name);
			om_file_name = g_strdup (file);
		}
		ui_message ("Saved.");
	}
	iks_delete (x);
}

static void
cb_open (void)
{
	select_file (FALSE, "Open ...", ui_open, NULL);
}

static void
cb_save (void)
{
	if (om_file_name)
		ui_save (NULL, NULL);
	else
		select_file (TRUE, "Save As ...", ui_save, NULL);
}

static void
cb_save_as (void)
{
	select_file (TRUE, "Save As ...", ui_save, NULL);
}

static void
ui_export (char *file, gpointer data)
{
	iks *x;

	x = ui_serialize_om ();
	export_lyx (x, file);
	iks_delete (x);
}

static void
cb_export (void)
{
	select_file (TRUE, "Export As ...", ui_export, NULL);
}

static void
cb_menu_add (GtkWidget *w, int flag)
{
	switch (flag) {
		case 0: cb_add_node ("(new)"); break;
		case 1: cb_add_method ("(new)"); break;
		case 2: cb_add_property ("(new)"); break;
	}
}

static void
cb_csl_open (void)
{
	csl_open ();
}

static void
cb_csl_template (void)
{
	iks *x;

	x = om_tree_get_current(OM_TREE(w_om_tree));
	csl_template(x);
	iks_delete(x);
}

static void
cb_update (OMTree *tree, struct OMTreeSelectSig *ssig, gpointer data)
{
	om_node_edit(OM_NODE(w_om_node), ssig->name, ssig->type, ssig->x);
}

void
ui_setup (void)
{
	GtkItemFactoryEntry menus[] = {
		{ _("/_File"), NULL, NULL, 0, "<Branch>" },
		{ _("/File/_Open ..."), "", cb_open, 0, "<StockItem>", GTK_STOCK_OPEN },
		{ _("/File/_Save"), "", cb_save, 0, "<StockItem>", GTK_STOCK_SAVE },
		{ _("/File/Save _As ..."), "", cb_save_as, 0, "<StockItem>", GTK_STOCK_SAVE_AS },
		{ _("/File/separator"), NULL, NULL, 0, "<Separator>" },
		{ _("/File/_Export LyX ..."), "", cb_export, 0, "<StockItem>", GTK_STOCK_CONVERT },
		{ _("/File/separator"), NULL, NULL, 0, "<Separator>" },
		{ _("/File/_Quit"), NULL, gtk_main_quit, 0, "<StockItem>", GTK_STOCK_QUIT },
		{ _("/_Edit"), NULL, NULL, 0, "<Branch>" },
		{ _("/Edit/Add _Object"), "<ctrl>n", cb_menu_add, 0, "<StockItem>", GTK_STOCK_ADD },
		{ _("/Edit/Add _Method"), "<ctrl>m", cb_menu_add, 1, "<StockItem>", GTK_STOCK_ADD },
		{ _("/Edit/Add _Property"), "<ctrl>p", cb_menu_add, 2, "<StockItem>", GTK_STOCK_ADD },
		{ _("/Edit/separator"), NULL, NULL, 0, "<Separator>" },
		{ _("/Edit/Create CSL Template"), NULL, cb_csl_template, 0, NULL, NULL },
		{ _("/Edit/Open CSL Script ..."), NULL, cb_csl_open, 0, NULL, GTK_STOCK_OPEN },
		{ _("/_View"), NULL, NULL, 0, "<Branch>" },
	};
	GtkItemFactory *factory;
	GtkAccelGroup *agrp;
	gint n = sizeof (menus) / sizeof (menus[0]);

	GtkWidget *w;
	GtkWidget *vb, *hb, *menu, *sw;
	GtkWidget *vb2, *hb2, *b, *frame;

	// pencere
	w = gtk_window_new (GTK_WINDOW_TOPLEVEL);
	main_window = w;
	gtk_window_set_title (GTK_WINDOW (w), _("COMAR OM Editor"));
	gtk_window_set_role (GTK_WINDOW (w), "omed_main");
	gtk_window_set_default_size (GTK_WINDOW (w), 600, 340);
	g_signal_connect (G_OBJECT (w), "delete_event", G_CALLBACK (gtk_main_quit), NULL);

	vb = gtk_vbox_new (FALSE, 1);
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

	hb = gtk_hpaned_new ();
	gtk_widget_show (hb);
	gtk_box_pack_start (GTK_BOX (vb), hb, TRUE, TRUE, 0);
	gtk_container_set_border_width (GTK_CONTAINER (hb), 2);

	frame = gtk_frame_new (NULL);
	gtk_widget_show (frame);
	gtk_frame_set_shadow_type (GTK_FRAME (frame), GTK_SHADOW_IN);
	gtk_paned_add1 (GTK_PANED (hb), frame);

	// new node tree
	vb2 = gtk_vbox_new (FALSE, 1);
	gtk_widget_show (vb2);
	gtk_container_add (GTK_CONTAINER (frame), vb2);

	sw = gtk_scrolled_window_new (NULL, NULL);
	gtk_widget_show (sw);
	gtk_scrolled_window_set_shadow_type (GTK_SCROLLED_WINDOW (sw), GTK_SHADOW_ETCHED_IN);
	gtk_scrolled_window_set_policy (GTK_SCROLLED_WINDOW (sw), GTK_POLICY_AUTOMATIC, GTK_POLICY_ALWAYS);
	gtk_box_pack_start (GTK_BOX (vb2), sw, TRUE, TRUE, 0);

	w_om_tree = om_tree_new();
	gtk_widget_show (w_om_tree);
	gtk_container_add (GTK_CONTAINER (sw), w_om_tree);
	g_signal_connect(G_OBJECT(w_om_tree), "om-tree-select", G_CALLBACK(cb_update), NULL);

	// node tree buttons
	hb2 = gtk_hbox_new (TRUE, 3);
	gtk_widget_show (hb2);
	gtk_container_set_border_width (GTK_CONTAINER (hb2), 1);
	gtk_box_pack_start (GTK_BOX (vb2), hb2, FALSE, TRUE, 0);

	b = pix_button (om_stock_id(OM_OBJECT), _("Add Object"));
	gtk_container_add (GTK_CONTAINER (hb2), b);
	g_signal_connect_swapped (G_OBJECT (b), "clicked", G_CALLBACK (cb_add_node), "(new)");

	b = pix_button (om_stock_id(OM_METHOD), _("Add Method"));
	gtk_container_add (GTK_CONTAINER (hb2), b);
	g_signal_connect_swapped (G_OBJECT (b), "clicked", G_CALLBACK (cb_add_method), "(new)");

	b = pix_button (om_stock_id(OM_PROPERTY), _("Add Property"));
	gtk_container_add (GTK_CONTAINER (hb2), b);
	g_signal_connect_swapped (G_OBJECT (b), "clicked", G_CALLBACK (cb_add_property), "(new)");

	b = pix_button (GTK_STOCK_REMOVE, "Remove");
	gtk_container_add (GTK_CONTAINER (hb2), b);
	g_signal_connect_swapped (G_OBJECT (b), "clicked", G_CALLBACK (cb_remove_node), NULL);

	// node info
	frame = gtk_frame_new (NULL);
	gtk_widget_show (frame);
	gtk_frame_set_shadow_type (GTK_FRAME (frame), GTK_SHADOW_IN);
	gtk_paned_add2 (GTK_PANED (hb), frame);

	w_om_node = om_node_new();
	gtk_container_set_border_width(GTK_CONTAINER(w_om_node), 3);
	gtk_widget_show(w_om_node);
	gtk_container_add(GTK_CONTAINER(frame), w_om_node);

	// status bar
	status = gtk_statusbar_new ();
	status_id = gtk_statusbar_get_context_id (GTK_STATUSBAR (status), "omed");
	gtk_widget_show (status);
	gtk_box_pack_start (GTK_BOX (vb), status, FALSE, FALSE, 0);

	// initial namespace
	om_tree_add(OM_TREE(w_om_tree), OM_NAMESPACE, "COMAR");

	gtk_widget_show (w);
}

void
ui_message (char *msg)
{
	gtk_statusbar_push (GTK_STATUSBAR (status), status_id, msg);
}
