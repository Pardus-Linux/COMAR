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

int db_open_storage(int node_no, const char *app);
int db_get_data(const char *key, char **bufferp, size_t *sizep);
int db_put_data(const char *key, const char *buffer, size_t size);
void db_close_storage(void);

int db_get_acl(int node_no, char **bufferp, size_t *sizep);
int db_put_acl(int node_no, const char *buffer, size_t size);


#endif /* DB_H */
