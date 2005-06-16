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
	unsigned int cmd;
	unsigned int data_size;
};

struct ProcChild {
	int from;
	int to;
	pid_t pid;
	void *data;
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

// ipc commands
enum {
	CMD_DIED,
	CMD_QUIT,
	CMD_CALL,
	CMD_FAIL,
	CMD_RESULT
};

// for readability of send_cmd/data functions
#define TO_PARENT NULL

void proc_init(void);
struct ProcChild *proc_fork(void (*child_func)(void));
int proc_listen(struct ProcChild **sender, int timeout);
int proc_send_cmd(struct ProcChild *child, int cmd, unsigned int data_size);
int proc_send_data(struct ProcChild *child, const char *data, unsigned int size);
int proc_get_data(struct ProcChild *p, char **bufferptr);


#endif /* PROCESS_H */
