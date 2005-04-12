/*
** Copyright (c) 2004, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - om-tree.h
** widget header for editing the om tree
*/

#ifndef OM_TREE_H
#define OM_TREE_H

#define OM_TYPE_TREE (om_tree_get_type())
#define OM_TREE(obj) (G_TYPE_CHECK_INSTANCE_CAST((obj), OM_TYPE_TREE , OMTree))
#define OM_TREE_CLASS(klass) (G_TYPE_CHECK_CLASS_CAST((klass), OM_TYPE_TREE , OMTreeClass))

typedef struct _OMTree OMTree;
typedef struct _OMTreeClass OMTreeClass;

struct _OMTree {
	GtkTreeView tree;
	GtkTreeStore *t_store;
	GtkTreeSelection *t_select;
	GtkTreeViewColumn *t_col;
	GtkCellRenderer *t_cell;
};

struct OMTreeSelectSig {
	char *name;
	int type;
	iks *x;
};

struct _OMTreeClass {
	GtkTreeViewClass parent_class;
	void (*om_tree_select)(OMTree *obj, struct OMTreeSelectSig *ssig);
};

GType om_tree_get_type(void);
GtkWidget *om_tree_new(void);
int om_tree_set(OMTree *obj, iks *om);
iks *om_tree_get(OMTree *obj);
iks *om_tree_get_current(OMTree *obj);
void om_tree_clear(OMTree *obj);
void om_tree_add(OMTree *obj, int type, const char *name);
void om_tree_remove(OMTree *obj);

// useful utility functions
enum {
	OM_UNKNOWN,
	OM_NAMESPACE,
	OM_OBJECT,
	OM_METHOD,
	OM_PROPERTY
};

gchar *om_stock_id(int type);
int om_type(const char *name);
char *om_name(int type);


#endif	/* OM_TREE_H */
