/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - node-acl.h
** access control list editor widget header
*/

#ifndef OM_ACL_H
#define OM_ACL_H

#define OM_TYPE_ACL (om_acl_get_type ())
#define OM_ACL(obj) (G_TYPE_CHECK_INSTANCE_CAST ((obj), OM_TYPE_ACL , OMAcl))
#define OM_ACL_CLASS(klass) (G_TYPE_CHECK_CLASS_CAST ((klass), OM_TYPE_ACL , OMAclClass))

typedef struct _OMAcl OMAcl;
typedef struct _OMAclClass OMAclClass;

struct _OMAcl {
	GtkVBox vbox;
	GtkListStore *t_store;
	GtkWidget *t_view;
	GtkTreeSelection *t_select;
	GtkWidget *inherit_box;
	GtkWidget *inherit_combo;
	GtkWidget *label;
	iks *x;
	iks *acl;
};

struct _OMAclClass {
	GtkVBoxClass parent_class;
};

GType om_acl_get_type(void);
GtkWidget *node_acl_new(void);
void node_acl_edit(GtkWidget *w, iks *x);


#endif	/* OM_ACL_H */
