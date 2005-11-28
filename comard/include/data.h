/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#ifndef DB_H
#define DB_H 1

int db_init(void);

int db_put_script(int node_no, const char *app, const char *buffer, size_t size);
int db_del_app(const char *app);
int db_get_apps(int node_no, char **bufferp);
int db_get_code(int node_no, const char *app, char **bufferp, size_t *sizep);

int db_put_profile(int node_no, const char *app, const char *args, size_t args_size);
int db_dump_profile(void);


#endif /* DB_H */
