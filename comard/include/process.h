/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#ifndef PROCESS_H
#define PROCESS_H 1

struct ProcCmd {
	int cmd;
	unsigned int data_size;
};

struct ProcChild {
	int from;
	int to;
	pid_t pid;
	int state;
	struct ProcCmd cmd;
};

struct Proc {
	// parent info
	struct ProcChild parent;
	// children info
	int nr_children;
	int max_children;
	struct ProcChild *children;
};

// per process global variable
extern struct Proc my_proc;

void proc_init(void);
struct ProcChild *proc_fork(void (*child_func)(void));
int proc_listen(struct ProcChild **sender, int timeout);
int proc_cmd_to_parent(int cmd, unsigned int data_size);
int proc_data_to_parent(const char *data, unsigned int size);
int proc_cmd_to_child(struct ProcChild *child, int cmd, unsigned int data_size);
int proc_data_to_child(struct ProcChild *child, const char *data, unsigned int size);
int proc_read_data(struct ProcChild *sender, char *buffer);


#endif /* PROCESS_H */
