/*
** Copyright (c) 2004, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - node-retval.h
** return value widget header
*/

#ifndef NODE_RETVAL_H
#define NODE_RETVAL_H

#include "om-node.h"

#define NODE_TYPE_RETVAL (node_retval_get_type())
#define NODE_RETVAL(obj) (G_TYPE_CHECK_INSTANCE_CAST((obj), NODE_TYPE_RETVAL , NodeRetval))
#define NODE_RETVAL_CLASS(klass) (G_TYPE_CHECK_CLASS_CAST((klass), NODE_TYPE_RETVAL , NodeRetvalClass))

typedef struct _NodeRetval NodeRetval;
typedef struct _NodeRetvalClass NodeRetvalClass;

struct _NodeRetval {
	GtkVBox vbox;
	iks *x;
	GtkWidget *combo, *rw_combo, *rw_label, *loc;
};

struct _NodeRetvalClass {
	GtkVBoxClass parent_class;
};

GType node_retval_get_type(void);
GtkWidget *node_retval_new(void);
void node_retval_edit(GtkWidget *w, iks *x);
struct OMNodeEditor *node_retval_get_editor(void);


#endif	/* NODE_RETVAL_H */
