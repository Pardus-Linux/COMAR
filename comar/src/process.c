/*
** Copyright (c) 2005-2007, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <string.h>
#include <sys/time.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#include <dbus/dbus.h>
#include <time.h>

#include "cfg.h"
#include "dbus.h"
#include "log.h"
#include "process.h"

//! Struct that holds active process' information
struct Proc my_proc;

//! Whether a shutdown has been requested
int shutdown_activated = 0;

//! Process name
static char *name_addr;

//! Size of process name
static size_t name_size;

//! Signal handler
static void
handle_sigterm(int signum)
{
    shutdown_activated = 1;
}

//! Activates signal handling
static void
handle_signals(void)
{
    struct sigaction act;
    struct sigaction ign;
    struct sigaction dfl;

    act.sa_handler = handle_sigterm;
    /*! initialize and empty a signal set. Signals are to be blocked while executing handle_sigterm */
    sigemptyset(&act.sa_mask);
    act.sa_flags = 0; /*!< special flags */

    ign.sa_handler = SIG_IGN;
    sigemptyset(&ign.sa_mask);
    ign.sa_flags = 0;

    dfl.sa_handler = SIG_DFL;
    sigemptyset(&dfl.sa_mask);
    dfl.sa_flags = 0;

    sigaction(SIGTERM, &act, NULL);
    sigaction(SIGPIPE, &ign, NULL);
    sigaction(SIGINT, &dfl, NULL);
}

//! Sets process name
static void
set_my_name(const char *name)
{
    /*!
     * Sets new process name. Variables must be initialized with
     * proc_init() before using this function.
     *
     * @name Process name
     */

    if (my_proc.parent.from == -1) {
        return;
    }

    if (strlen(name) + 1 < name_size) {
        memset(name_addr, 0, name_size);
        strcpy(name_addr, name);
    }
}

//! Initializes main process
int
proc_init(int argc, char *argv[], const char *name)
{
    /*!
     * Initializes main process. Gets name address, size, and
     * initializes signal handler. Creates pidfile if bus type
     * is system.
     *
     * @argc Number of arguments
     * @argv Array of arguments
     * @name Process name
     */

    int i;

    name_addr = argv[0];
    name_size = 0;
    for (i = 0; i < argc; i++) {
        name_size += strlen(argv[i]) + 1;
    }

    memset(&my_proc, 0, sizeof(struct Proc));
    my_proc.parent.to = -1;
    my_proc.parent.from = -1;
    my_proc.desc = name;
    my_proc.max_children = 8;
    my_proc.children = calloc(8, sizeof(struct ProcChild));
    handle_signals();
    set_my_name(my_proc.desc);

    FILE *f = fopen(cfg_pid_name, "w");
    if (f) {
        fprintf(f, "%d", getpid());
        fclose(f);
    }
    else {
        printf("Can't create pid file '%s'\n", cfg_pid_name);
        return 1;
    }

    return 0;
}

//! Appends child process' information to parent's info table
static struct ProcChild *
add_child(pid_t pid, int to, int from, DBusMessage *bus_msg, const char *desc)
{
    /*!
     * Appends child process' information to parent's info table.
     *
     * @pid Process ID
     * @to Input FD
     * @from Output FD
     * @bus_msg DBus message
     * @desc Process description
     * @return ProcChild node
     */

    int i;

    i = my_proc.nr_children;
    if (i >= my_proc.max_children) {
        if (i == 0) {
            my_proc.max_children = 4;
        } else {
            my_proc.max_children *= 2;
        }
        my_proc.children = realloc(my_proc.children,
            my_proc.max_children * sizeof(struct ProcChild)
        );
    }
    memset(&my_proc.children[i], 0, sizeof(struct ProcChild));
    my_proc.children[i].from = from;
    my_proc.children[i].to = to;
    my_proc.children[i].pid = pid;
    my_proc.children[i].bus_msg = bus_msg;
    my_proc.children[i].desc = desc;
    ++my_proc.nr_children;
    return &my_proc.children[i];
}

//! Removes child process' information from parent's info table
void
rem_child(int nr)
{
    /*!
     * Removes child process' information from parent's info table
     *
     * @nr Index
     */

    int status;
    waitpid(my_proc.children[nr].pid, &status, 0);
    close(my_proc.children[nr].to);
    close(my_proc.children[nr].from);
    --my_proc.nr_children;
    if (0 == my_proc.nr_children) return;
    (my_proc.children)[nr] = (my_proc.children)[my_proc.nr_children];
}

//! Stops all children processes
static void
stop_children(void)
{
    /*!
     * Stops all children processes.
     */

    struct timeval start;
    struct timeval cur;
    struct timeval tv;
    unsigned long msec;
    fd_set fds;
    int i, sock, max;
    int len;
    char tmp[100];

    // hey kiddo, finish your homework and go to bed
    for (i = 0; i < my_proc.nr_children; i++) {
        kill(my_proc.children[i].pid, SIGTERM);
    }

    gettimeofday(&start, NULL);
    msec = 0;

    while (my_proc.nr_children && msec < 3000) {
        // 1/5 second precision for the 3 second maximum shutdown time
        tv.tv_sec = 0;
        tv.tv_usec = 200000;
        max = 0;
        FD_ZERO(&fds);
        for (i = 0; i < my_proc.nr_children; i++) {
            sock = my_proc.children[i].from;
            FD_SET(sock, &fds);
            if (sock > max) max = sock;
        }
        ++max;

        if (select(max, &fds, NULL, NULL, &tv) > 0) {
            for (i = 0; i < my_proc.nr_children; i++) {
                sock = my_proc.children[i].from;
                if (FD_ISSET(sock, &fds)) {
                    len = read(sock, &tmp, sizeof(tmp));
                    if (0 == len) {
                        rem_child(i);
                    }
                }
            }
        }

        gettimeofday(&cur, NULL);
        msec = (cur.tv_sec * 1000) + (cur.tv_usec / 1000);
        msec -= (start.tv_sec * 1000) + (start.tv_usec / 1000);
    }

    // sorry kids, play time is over
    for (i = 0; i < my_proc.nr_children; i++) {
        kill(my_proc.children[i].pid, SIGKILL);
    }
}

//! Ends a process
void
proc_finish(void)
{
    /*!
     * End a process and it's children.
     */

    if (my_proc.nr_children) stop_children();
    log_debug(LOG_PROC, "%s process %d ended\n", my_proc.desc, getpid());
    exit(0);
}

//! Ends process if a shutdown is requested
void
proc_check_shutdown(void)
{
    if (shutdown_activated) {
        if (my_proc.parent.from != -1)
            proc_finish();
    }
}

//! Forks a function
struct ProcChild *
proc_fork(void (*child_func)(void), const char *desc, DBusConnection *bus_conn, DBusMessage *bus_msg)
{
    /*
     * Forks a function.
     *
     * @child_func Function to be forked
     * @desc Process description
     * @bus_conn Related DBus connection, if there's one
     * @bus_msg Related DBus message, if there's one
     * @return ProcChild node
     */

    pid_t pid;
    int fdr[2], fdw[2];
    int i;

    pipe(fdr);
    pipe(fdw);
    pid = fork();
    if (pid == -1) return NULL;

    if (pid == 0) {
        // new child process starts
        // we have to close unneeded pipes inherited from the parent
        if (my_proc.parent.to != -1) close(my_proc.parent.to);
        if (my_proc.parent.from != -1) close(my_proc.parent.from);
        for (i = 0; i < my_proc.nr_children; i++) {
            close(my_proc.children[i].to);
            close(my_proc.children[i].from);
        }
        close(fdw[1]);
        close(fdr[0]);
        // stop parent's pipes from propagating through an exec()
        fcntl(fdw[0], F_SETFD, FD_CLOEXEC);
        fcntl(fdr[1], F_SETFD, FD_CLOEXEC);
        // now setup our own data
        memset(&my_proc, 0, sizeof(struct Proc));
        my_proc.parent.from = fdw[0];
        my_proc.parent.to = fdr[1];
        my_proc.parent.pid = getppid();
        my_proc.desc = desc;
        my_proc.locale = dbus_caller_locale(bus_msg);
        my_proc.bus_conn = bus_conn;
        my_proc.bus_msg = bus_msg;
        handle_signals();
        set_my_name(desc);
        log_debug(LOG_PROC, "%s process %d started\n", desc, getpid());
        // finally jump to the real function
        child_func();
        proc_finish();
        while (1) {} // to keep gcc happy
    } else {
        // parent process continues
        close(fdw[0]);
        close(fdr[1]);
        return add_child(pid, fdw[1], fdr[0], bus_msg, desc);
    }
}

//! Gets active process' parent and children FD's
static int
proc_setup_fds(fd_set *fds)
{
    /*!
     * Gets active process' parent and children FD's
     *
     * @fds File descriptor set pointer
     * @return Number of file descriptors
     */

    int sock;
    int i;
    int max = 0;

    proc_check_shutdown();

    FD_ZERO(fds);
    sock = my_proc.parent.from;
    if (sock != -1) {
        // we have a parent to listen for
        FD_SET(sock, fds);
        if (sock > max) max = sock;
    }
    // and some children maybe?
    for (i = 0; i < my_proc.nr_children; i++) {
        sock = my_proc.children[i].from;
        FD_SET(sock, fds);
        if (sock > max) max = sock;
    }

    return ++max;
}

//! Waits for incoming messages and remove children or kill process if required
static int
proc_select_fds(fd_set *fds, int max, struct ProcChild **senderp, size_t *sizep, int timeout_sec, int timeout_usec)
{
    /*!
     * Waits for incoming messages and remove children or kill process if required
     *
     * @fds File descriptor set
     * @max Number of FDSs
     * @sender Parent process' pointer
     * @sizep Size pointer
     * @timeout_sec Timeout in seconds
     * @timeout_usec Timeout in miliseconds
     * @return 1 if there's a message, 0 else
     */

    unsigned int ipc;
    struct timeval tv, *tvptr;
    int sock;
    int len;
    int i;

    tv.tv_sec = timeout_sec;
    tv.tv_usec = timeout_usec;
    if (timeout_sec != -1) tvptr = &tv; else tvptr = NULL;

    if (select(max, fds, NULL, NULL, tvptr) > 0) {
        sock = my_proc.parent.from;
        if (sock != -1 && FD_ISSET(sock, fds)) {
            len = read(sock, &ipc, sizeof(ipc));
            if (0 == len) {
                // parent process left us
                // tell me that there is something worth living for tonight
                log_debug(LOG_PROC, "Parent left %s process %d\n", my_proc.desc, getpid());
                proc_finish();
            }
            *senderp = &my_proc.parent;
            *sizep = (ipc & 0x00FFFFFF);
            return 1;
        }
        for (i = 0; i < my_proc.nr_children; i++) {
            sock = my_proc.children[i].from;
            if (FD_ISSET(sock, fds)) {
                len = read(sock, &ipc, sizeof(ipc));
                if (len == sizeof(ipc)) {
                    *senderp = &my_proc.children[i];
                    *sizep = (ipc & 0x00FFFFFF);
                    return 1;
                } else {
                    rem_child(i);
                    *senderp = NULL;
                    *sizep = 0;
                    return 1;
                }
            }
        }
        *senderp = NULL;
        *sizep = 0;
        return 1;
    }
    return 0;
}

//! Listen for incoming messages to active process.
int
proc_listen(struct ProcChild **senderp, size_t *sizep, int timeout_sec, int timeout_usec)
{
    /*!
     * Gets active process' parent and children FD's then waits for
     * incoming messages and remove children or kill process if required.
     *
     * @sender Parent process' pointer
     * @sizep Size pointer
     * @timeout_sec Timeout in seconds
     * @timeout_usec Timeout in miliseconds
     * @return 1 if there's a message, 0 else
     */

    fd_set fds;
    int max;

    max = proc_setup_fds(&fds);

    return proc_select_fds(&fds, max, senderp, sizep, timeout_sec, timeout_usec);
}
