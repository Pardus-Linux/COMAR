/*
** Copyright (c) 2005-2006, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#ifndef CSL_H
#define CSL_H 1

#include "utility.h"

enum {
	CSL_OK = 0,
	CSL_NOMEM,
	CSL_BADCODE,
	CSL_NOFUNC,
	CSL_FUNCERR
};

void csl_setup(void);
int csl_compile(char *str, char *name, char **codeptr, size_t *sizeptr);
int csl_execute(char *code, size_t size, const char *func_name, struct pack *pak, char **resptr, int *reslen);
void csl_cleanup(void);


#endif /* CSL_H */
