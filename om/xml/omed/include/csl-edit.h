/*
** Copyright (c) 2004, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - csl-edit.h
** csl editor widget header
*/

#ifndef CSL_EDIT_H
#define CSL_EDIT_H

#include <gtksourceview/gtksourceview.h>
#include <gtksourceview/gtksourcetag.h>

#define CSL_TYPE_EDIT (csl_edit_get_type())
#define CSL_EDIT(obj) (G_TYPE_CHECK_INSTANCE_CAST((obj), CSL_TYPE_EDIT , CSLEdit))
#define CSL_EDIT_CLASS(klass) (G_TYPE_CHECK_CLASS_CAST((klass), CSL_TYPE_EDIT , CSLEditClass))

typedef struct _CSLEdit CSLEdit;
typedef struct _CSLEditClass CSLEditClass;

struct _CSLEdit {
	GtkWindow window;
	GtkWidget *source_view;
	GtkSourceBuffer *sbuf;
	GtkWidget *status;
	gint status_id;
};

struct _CSLEditClass {
	GtkWindowClass parent_class;
};

GType csl_edit_get_type(void);
GtkWidget *csl_edit_new(void);

void csl_template(iks *x);
void csl_open(void);


#endif	/* CSL_EDIT_H */
