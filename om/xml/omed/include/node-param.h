/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - node-param.h
** method parameters widget header
*/

#ifndef NODE_PARAM_H
#define NODE_PARAM_H

#include "om-node.h"

#define NODE_TYPE_PARAM (node_param_get_type())
#define NODE_PARAM(obj) (G_TYPE_CHECK_INSTANCE_CAST((obj), NODE_TYPE_PARAM , NodeParam))
#define NODE_PARAM_CLASS(klass) (G_TYPE_CHECK_CLASS_CAST((klass), NODE_TYPE_PARAM , NodeParamClass))

typedef struct _NodeParam NodeParam;
typedef struct _NodeParamClass NodeParamClass;

struct _NodeParam {
	GtkVBox vbox;
	iks *x;
	iks *inputs;
	GtkWidget *t_view;
	GtkListStore *t_store;
	GtkTreeSelection *t_select;
};

struct _NodeParamClass {
	GtkVBoxClass parent_class;
};

GType node_param_get_type(void);
GtkWidget *node_param_new(void);
void node_param_edit(GtkWidget *w, iks *x);
struct OMNodeEditor *node_param_get_editor(void);


#endif	/* NODE_PARAM_H */
