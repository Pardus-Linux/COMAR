/*
** Copyright (c) 2005-2006, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#ifndef JOB_H
#define JOB_H 1

#include "process.h"
#include "utility.h"

int job_start(int cmd, struct ipc_struct *ipc, struct pack *pak);


#endif /* JOB_H */
