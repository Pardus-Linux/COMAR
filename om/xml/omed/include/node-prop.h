/*
** Copyright (c) 2004, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - node-prop.h
** property attributes widget header
*/

#ifndef NODE_PROP_H
#define NODE_PROP_H

#include "om-node.h"

#define NODE_TYPE_PROP (node_prop_get_type())
#define NODE_PROP(obj) (G_TYPE_CHECK_INSTANCE_CAST((obj), NODE_TYPE_PROP , NodeProp))
#define NODE_PROP_CLASS(klass) (G_TYPE_CHECK_CLASS_CAST((klass), NODE_TYPE_PROP , NodePropClass))

typedef struct _NodeProp NodeProp;
typedef struct _NodePropClass NodePropClass;

struct _NodeProp {
	GtkVBox vbox;
	iks *x;
	GtkWidget *combo;
	GtkWidget *loc;
};

struct _NodePropClass {
	GtkVBoxClass parent_class;
};

GType node_prop_get_type(void);
GtkWidget *node_prop_new(void);
void node_prop_edit(GtkWidget *w, iks *x);
struct OMNodeEditor *node_prop_get_editor(void);


#endif	/* NODE_PROP_H */
