/*
** Copyright (c) 2005-2007, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

int db_init(void);
int db_get_apps(char **bufferp);
int db_get_app_models(char *app, char **bufferp);
int db_get_model_apps(char *model, char **bufferp);
int db_register_model(char *app, char *model);
int db_remove_app(char *app);
int db_check_app(char *app);
int db_check_model(char *app, char *model);

char *get_script_path(const char *interface, const char *path);
