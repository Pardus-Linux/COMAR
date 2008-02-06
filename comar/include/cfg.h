/*
** Copyright (c) 2005-2007, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

extern char *cfg_bus_socket;
extern char *cfg_bus_name;
extern char *cfg_bus_interface;
extern char *cfg_config_dir;
extern char *cfg_data_dir;
extern int cfg_timeout;
extern int cfg_log_console;
extern int cfg_log_file;
extern char *cfg_log_file_name;
extern char *cfg_pid_name;
extern int cfg_log_flags;

void cfg_init(int argc, char *argv[]);
