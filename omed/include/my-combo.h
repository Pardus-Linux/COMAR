/*
** Copyright (c) 2004, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

/*
** OMED - my-combo.h
** cell editable combo box widget header
*/

#ifndef MY_COMBO_H
#define MY_COMBO_H

#define MY_TYPE_COMBO (my_combo_get_type())
#define MY_COMBO(obj) (G_TYPE_CHECK_INSTANCE_CAST((obj), MY_TYPE_COMBO , MyCombo))
#define MY_COMBO_CLASS(klass) (G_TYPE_CHECK_CLASS_CAST((klass), MY_TYPE_COMBO , MyComboClass))

typedef struct _MyCombo MyCombo;
typedef struct _MyComboClass MyComboClass;

struct _MyCombo {
	GtkComboBox combo;
};

struct _MyComboClass {
	GtkComboBoxClass parent_class;
};

GType my_combo_get_type(void);
GtkWidget *my_combo_new(void);


#endif	/* MY_COMBO_H */
