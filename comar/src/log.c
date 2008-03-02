/*
** Copyright (c) 2005-2006, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <unistd.h>
#include <time.h>
#include <sys/stat.h>

#include "cfg.h"
#include "log.h"
#include "process.h"

//! Puts time into f
static void
timestamp(FILE *f)
{
    static char buf[128];
    time_t t;
    struct tm *bt;

    time(&t);
    bt = localtime(&t);
    strftime(buf, 127, "%F %T ", bt);
    fputs(buf, f);
}

//! Prints comar version info and process id to stdout
static void
pidstamp(FILE *f)
{
    if (strlen(my_proc.desc) <= 5) {
        fprintf(f, "(%s-%d) ", my_proc.desc, getpid());
    }
    else {
        if (my_proc.bus_msg) {
            const char *sender = dbus_message_get_sender(my_proc.bus_msg);
            fprintf(f, "(%s-%d) [bus%s] ", my_proc.desc + 5, getpid(), sender);
        }
        else {
            fprintf(f, "(%s-%d) ", my_proc.desc + 5, getpid());
        }
    }
}

//! Print log
static void
log_print(const char *fmt, va_list ap, int error)
{
    /*!
     * Writes log to file (cfg_log_file_name) or stdout according to cfg_log_* options.
     *
     * @fmt Format string
     * @ap Argument list
     * @error 1 if this is an error message
     */

    if (cfg_log_console) {
        pidstamp(stdout);
        if (error) printf("Error: ");
        vprintf(fmt, ap);
    }

    if (cfg_log_file) {
        FILE *f;

        f = fopen(cfg_log_file_name, "a");
        if (f) {
            timestamp(f);
            pidstamp(f);
            if (error) fprintf(f, "Error: ");
            vfprintf(f, fmt, ap);
            fclose(f);
        }
    }

    // FIXME: syslog?
}

//! Log starter. Permissions of log file are set here
int
log_start(void)
{
    if (cfg_log_file) {
        FILE *f = fopen(cfg_log_file_name, "a");
        if (f) {
            fclose(f);
        }
        else {
            printf("Cannot write log file '%s'\n", cfg_log_file_name);
            return -1;
        }
    }

    log_info("COMAR v%s\n", VERSION);
    if (cfg_log_file) {
        // make sure log is not readable by ordinary users
        chmod(cfg_log_file_name, S_IRUSR | S_IWUSR);
    }

    return 0;
}

//! Error logging
void
log_error(const char *fmt, ...)
{
    /*!
     * Same as log_info, if this function is called instead, writes
     * information as an 'error' to log file
     */

    va_list ap;

    va_start(ap, fmt);
    log_print(fmt, ap, 1);
    va_end(ap);
}

//! Print log info
void
log_info(const char *fmt, ...)
{
    /*!
     * Prints log info of variable arguments with log_print function.
     * Console or file usage depends on cfg_log_* options
     *
     * @fmt Format string
     */

    va_list ap;

    va_start(ap, fmt);
    log_print(fmt, ap, 0);
    va_end(ap);
}

//! Log messages from sub processes for debugging
void
log_debug(int subsys, const char *fmt, ...)
{
    /*!
     * Same as log_info. If debug level doesn't match cfg_log_*
     * options, does nothing.
     *
     * @subsys Debug level
     * @fmt Format string
     */

    va_list ap;

    if ((cfg_log_flags & subsys) == 0)
        return;

    va_start(ap, fmt);
    log_print(fmt, ap, 0);
    va_end(ap);
}
