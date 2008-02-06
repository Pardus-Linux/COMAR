/*
** Copyright (c) 2005-2007, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <sys/stat.h>

#include "utility.h"

//! Returns part of a string
char *
strsub(const char *str, int start, int end)
{
    /*!
     * Returns part of a string.
     *
     * @str String
     * @start Where to start
     * @end Where to end
     * @return Requested part
     */

    if (start < 0) {
        start = strlen(str) + start;
    }
    if (start > strlen(str)) {
        start = 0;
    }
    if (end == 0) {
        end = strlen(str);
    }
    else if (end < 0) {
        end = strlen(str) + end;
    }
    if (end > strlen(str)) {
        end = strlen(str);
    }

    char *new_src, *t;
    new_src = malloc(end - start + 2);
    for (t = (char *) str + start; t < str + end; t++) {
        new_src[t - (str + start)] = *t;
    }
    new_src[t - (str + start)] = '\0';
    return new_src;
}

//! Replaces chars in a string
char *
strrep(const char *str, char old, char new)
{
    /*!
     * Replaces chars in a string.
     *
     * @str String
     * @old Char to be replaced
     * @new Char to be replaced with
     * @return Replaced value
     */

    char *new_str, *t;

    new_str = strdup(str);

    for (t = new_str; *t != '\0'; t++) {
        if (*t == old) {
            *t = new;
        }
    }

    return new_str;
}

//! Test whether a path exists
int
check_file(const char *fname)
{
    /*!
     * Test whether a file path exists.
     *
     * @fname File name
     * @return 1 if true, 0 if false
     */

    struct stat fs;
    return (stat(fname, &fs) == 0);
}

//! Returns content of a file
unsigned char *
load_file(const char *fname, int *sizeptr)
{
    /*!
     * Returns content of a file.
     *
     * @fname File name
     * @sizeptr Size pointer of file content
     * @return File content
     */

    FILE *f;
    struct stat fs;
    size_t size;
    unsigned char *data;

    if (stat(fname, &fs) != 0) return NULL;
    size = fs.st_size;
    if (sizeptr) *sizeptr = size;

    data = malloc(size + 1);
    if (!data) return NULL;
    memset(data, 0, size + 1);

    f = fopen(fname, "rb");
    if (!f) {
        free(data);
        return NULL;
    }
    if (fread(data, size, 1, f) < 1) {
        free(data);
        return NULL;
    }
    fclose(f);

    return data;
}

//! Saves file content
int
save_file(const char *fname, const char *buffer, size_t size)
{
    /*!
     * Saves file content.
     *
     * @fname File name
     * @buffer File content
     * @size Size
     * @return 0 on success, -1 on file open error, -2 on write error.
    */

    FILE *f;

    f = fopen(fname, "wb");
    if (!f) return -1;
    if (fwrite(buffer, size, 1, f) < 1) {
        fclose(f);
        return -2;
    }
    fclose(f);
    return 0;
}

//! Returns difference between to time values.
unsigned long
time_diff(struct timeval *start, struct timeval *end)
{
    /*!
     * Returns difference between to time values.
     *
     * @start Start time
     * @end End time
     */

    unsigned long msec;

    msec = (end->tv_sec * 1000) + (end->tv_usec / 1000);
    msec -= (start->tv_sec * 1000) + (start->tv_usec / 1000);
    return msec;
}
