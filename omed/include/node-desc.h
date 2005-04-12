/*
** Copyright (c) 2004, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - node-desc.h
** node description editor widget header
*/

#ifndef NODE_DESC_H
#define NODE_DESC_H

#include "om-node.h"

#define NODE_TYPE_DESC (node_desc_get_type())
#define NODE_DESC(obj) (G_TYPE_CHECK_INSTANCE_CAST((obj), NODE_TYPE_DESC , NodeDesc))
#define NODE_DESC_CLASS(klass) (G_TYPE_CHECK_CLASS_CAST((klass), NODE_TYPE_DESC , NodeDescClass))

typedef struct _NodeDesc NodeDesc;
typedef struct _NodeDescClass NodeDescClass;

struct _NodeDesc {
	GtkVBox vbox;
	GtkTextBuffer *desc_buf;
	iks *x;
};

struct _NodeDescClass {
	GtkVBoxClass parent_class;
};

GType node_desc_get_type(void);
GtkWidget *node_desc_new(void);
void node_desc_edit(GtkWidget *w, iks *x);
struct OMNodeEditor *node_desc_get_editor(void);


#endif	/* NODE_DESC_H */
