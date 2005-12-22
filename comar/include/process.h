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

struct ProcChild {
	int from;
	int to;
	pid_t pid;
	const char *desc;
};

struct Proc {
	// parent info
	struct ProcChild parent;
	const char *desc;
	// children info
	int nr_children;
	int max_children;
	struct ProcChild *children;
};

// per process global variable
extern struct Proc my_proc;

// for readability of send_cmd/data functions
#define TO_PARENT NULL

void proc_init(void);
void proc_calc_name_space(int argc, char *argv[]);
struct ProcChild *proc_get_rpc(void);
struct ProcChild *proc_fork(void (*child_func)(void), const char *desc);
void proc_check_shutdown(void);
void proc_finish(void);
int proc_listen(struct ProcChild **senderp, int *cmdp, size_t *sizep, int timeout);
int proc_send(struct ProcChild *p, int cmd, const void *data, size_t data_size);
int proc_recv(struct ProcChild *p, void *datap, size_t size);
int proc_recv_to(struct ProcChild *p, void *data, size_t size);
char *proc_pid_name(struct ProcChild *p);


#endif /* PROCESS_H */
