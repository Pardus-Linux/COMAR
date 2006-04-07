/*
** Copyright (c) 2005, TUBITAK/UEKAE
**
** This program is free software; you can redistribute it and/or modify it
** under the terms of the GNU General Public License as published by the
** Free Software Foundation; either version 2 of the License, or (at your
** option) any later version. Please read the COPYING file.
*/

#ifndef I18N_H
#define I18N_H 1

#define ENABLE_NLS 1

#ifdef ENABLE_NLS
#    include <locale.h>
#    include <libintl.h>
#    define _(String) gettext(String)
#    ifdef gettext_noop
#        define N_(String) gettext_noop(String)
#    else
#        define N_(String) (String)
#    endif
#else
/* stubs that do something close enough */
#    define textdomain(String)
#    define bindtextdomain(Domain, Directory)
#    define bind_textdomain_codeset(Domain, Codeset)
#    define _(String) (String)
#    define N_(String) (String)
#    define gettext(String) (String)
#    define dgettext(Domain,Message) (Message)
#    define dcgettext(Domain,Message,Type) (Message)
#endif

#endif /* I18N_H */
