/*
** Copyright (c) 2004, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - node-oper.h
** node operating mode widget header
*/

#ifndef NODE_OPER_H
#define NODE_OPER_H

#include "om-node.h"

#define NODE_TYPE_OPER (node_oper_get_type())
#define NODE_OPER(obj) (G_TYPE_CHECK_INSTANCE_CAST((obj), NODE_TYPE_OPER , NodeOper))
#define NODE_OPER_CLASS(klass) (G_TYPE_CHECK_CLASS_CAST((klass), NODE_TYPE_OPER , NodeOperClass))

typedef struct _NodeOper NodeOper;
typedef struct _NodeOperClass NodeOperClass;

struct _NodeOper {
	GtkVBox vbox;
	iks *x;
	GtkWidget *sel_combo;
	GtkWidget *adv_combo;
};

struct _NodeOperClass {
	GtkVBoxClass parent_class;
};

GType node_oper_get_type(void);
GtkWidget *node_oper_new(void);
void node_oper_edit(GtkWidget *w, iks *x);
struct OMNodeEditor *node_oper_get_editor(void);


#endif	/* NODE_OPER_H */
