/*
** Copyright (c) 2005-2006, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#ifndef PROCESS_H
#define PROCESS_H 1

#include "utility.h"

extern int shutdown_activated;

struct ipc_source {
	void *chan;
	unsigned int cookie; /*!< To detect process */
	int id;
	unsigned char lang[4]; /*!< Messages language */
};

//! A basic process structure
struct ProcChild {
	int from; /*!< FIXME. */
	int to; /*!< FIXME. */
	pid_t pid; /*!< Process id */
	const char *desc; /*!< Description of process, also its name */
	// keep track of command source, used by job_cancel
	struct ipc_source source;
};

//! A Process
struct Proc {
	// parent info
	struct ProcChild parent; /*!< Parent of this process */
	const char *desc; /*!< Name of this process */
	// children info
	int nr_children; /*!< Number of children */
	int max_children; /*!< Maximum children */
	struct ProcChild *children;
};

struct ipc_struct {
	struct ipc_source source;
	int node;
};

extern struct Proc my_proc; /*!< Per process global variable */

//! For readability of send_cmd/data functions
#define TO_PARENT NULL

//! ipc commands
enum {
	CMD_FINISH = 0,
	CMD_RESULT,
	CMD_RESULT_START,
	CMD_RESULT_END,
	CMD_FAIL,
	CMD_NONE,
	CMD_ERROR,
	CMD_REGISTER,
	CMD_REMOVE,
	CMD_CALL,
	CMD_CALL_PACKAGE,
	CMD_CANCEL,
	CMD_GETLIST,
	CMD_NOTIFY,
	CMD_DUMP_PROFILE,
	CMD_SHUTDOWN,
	CMD_EVENT,
	CMD_CUSTOM
};

// functions
void proc_init(int argc, char *argv[]);
struct ProcChild *proc_get_rpc(void);

struct ProcChild *proc_fork(void (*child_func)(void), const char *desc);
void proc_check_shutdown(void);
void proc_finish(void);

int proc_setup_fds(fd_set *fds);
int proc_select_fds(fd_set *fds, int max, struct ProcChild **senderp, int *cmdp, size_t *sizep, int timeout);
int proc_listen(struct ProcChild **senderp, int *cmdp, size_t *sizep, int timeout);
int proc_put(struct ProcChild *p, int cmd, struct ipc_struct *ipc, struct pack *pak);
int proc_get(struct ProcChild *p, struct ipc_struct *ipc, struct pack *pak, size_t size);


#endif /* PROCESS_H */
