/*
** Copyright (c) 2005-2007, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <dbus/dbus.h>

struct ProcChild {
    int from;
    int to;
    pid_t pid;
    DBusMessage *bus_msg;
    const char *desc;
};

struct Proc {
    // parent info
    struct ProcChild parent;
    const char *desc;
    // children info
    int nr_children;
    int max_children;
    DBusConnection *bus_conn;
    DBusMessage *bus_msg;
    struct ProcChild *children;
};

extern struct Proc my_proc;
extern int shutdown_activated;

int proc_init(int argc, char *argv[], const char *name);
int proc_listen(struct ProcChild **senderp, size_t *sizep, int timeout_sec, int timeout_usec);
struct ProcChild *proc_fork(void (*child_func)(void), const char *desc, DBusConnection *bus_conn, DBusMessage *bus_msg);
void rem_child(int nr);
void proc_finish(void);
