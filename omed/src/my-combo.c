/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - my-combo.c
** cell editable combo box widget
*/

#include <gdk/gdkkeysyms.h>

#include "common.h"
#include "my-combo.h"

static void
my_combo_class_init(MyComboClass *class)
{
}

static void
my_combo_init(MyCombo *obj)
{
}

static void
cb_activate(GtkCellEditable *cell)
{
	gtk_cell_editable_editing_done(cell);
	gtk_cell_editable_remove_widget(cell);
}

static gboolean
cb_key_press(GtkCellEditable *cell, GdkEventKey *event)
{
	if (event->keyval == GDK_Escape) {
		// FIXME: cell->editing_cancelled = TRUE;
		gtk_cell_editable_editing_done(cell);
		gtk_cell_editable_remove_widget(cell);
		return TRUE;
	}
	if (event->keyval == GDK_Up || event->keyval == GDK_Down) {
		gtk_cell_editable_editing_done(cell);
		gtk_cell_editable_remove_widget(cell);
		return TRUE;
	}
	return FALSE;
}

static void
my_combo_start_editing(GtkCellEditable *cell, GdkEvent *event)
{
	g_signal_connect(cell, "changed", G_CALLBACK(cb_activate), NULL);
	g_signal_connect(cell, "key_press_event", G_CALLBACK(cb_key_press), NULL);
}

static void
my_combo_cell_editable_init(GtkCellEditableIface *iface)
{
	iface->start_editing = my_combo_start_editing;
}

GType
my_combo_get_type(void)
{
	static GType my_combo_type = 0;

	if (!my_combo_type) {
		static const GTypeInfo my_combo_info = {
			sizeof (MyComboClass),
			NULL,
			NULL,
			(GClassInitFunc) my_combo_class_init,
			NULL,
			NULL,
			sizeof (MyCombo),
			0,
			(GInstanceInitFunc) my_combo_init
		};
		static const GInterfaceInfo cell_editable_info = {
			(GInterfaceInitFunc) my_combo_cell_editable_init,
			NULL,
			NULL
		};
		my_combo_type = g_type_register_static(GTK_TYPE_COMBO_BOX, "MyCombo", &my_combo_info, 0);
		g_type_add_interface_static(my_combo_type, GTK_TYPE_CELL_EDITABLE, &cell_editable_info);
	}
	return my_combo_type;
}

GtkWidget *
my_combo_new(void)
{
	return GTK_WIDGET(g_object_new(my_combo_get_type(), NULL));
}
