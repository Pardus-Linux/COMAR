/*
** Copyright (c) 2004, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - om-node.h
** widget header for editing an om node
*/

#ifndef OM_NODE_H
#define OM_NODE_H

#define OM_TYPE_NODE (om_node_get_type())
#define OM_NODE(obj) (G_TYPE_CHECK_INSTANCE_CAST((obj), OM_TYPE_NODE , OMNode))
#define OM_NODE_CLASS(klass) (G_TYPE_CHECK_CLASS_CAST((klass), OM_TYPE_NODE , OMNodeClass))

typedef struct _OMNode OMNode;
typedef struct _OMNodeClass OMNodeClass;

typedef void (OMNodeEditFunc)(GtkWidget *w, iks *x);

struct OMNodeEditor {
	struct OMNodeEditor *next;
	GtkWidget *w;
	gboolean expand;
	int types;
	OMNodeEditFunc *edit_func;
};

struct _OMNode {
	GtkVBox vbox;
	GtkWidget *icon;
	GtkWidget *name;
	GtkWidget *edit_area;
	struct OMNodeEditor *editors;
};

struct _OMNodeClass {
	GtkVBoxClass parent_class;
};

GType om_node_get_type(void);
GtkWidget *om_node_new(void);
void om_node_edit(OMNode *obj, const char *name, int type, iks *x);
void om_node_stop_editing(OMNode *obj);


#endif	/* OM_NODE_H */
