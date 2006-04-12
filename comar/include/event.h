/*
** Copyright (c) 2005-2006, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#ifndef EVENT_H
#define EVENT_H 1

enum {
	EVENT_KERNEL,
	EVENT_NOTIFY,
	EVENT_MAX
};

void event_start(void);


#endif /* EVENT_H */
