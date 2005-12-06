/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#ifndef CFG_H
#define CFG_H 1

extern char *cfg_model_file;
extern char *cfg_data_dir;
extern char *cfg_socket_name;
extern int cfg_log_console;
extern int cfg_log_file;
extern char *cfg_log_file_name;
extern int cfg_log_flags;

void cfg_init(int argc, char *argv[]);


#endif /* CFG_H */
