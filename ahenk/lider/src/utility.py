#
# Copyright (C) 2007, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

from kdecore import *

def I18N_NOOP(x):
    return x

def getIconSet(name, group=KIcon.Toolbar):
    return KGlobal.iconLoader().loadIconSet(name, group)

def getIcon(name, group=KIcon.Toolbar):
    return KGlobal.iconLoader().loadIcon(name, group)

def saltedSHA(password):
    import base64
    import sha
    import random
    
    chars = "".join([chr(x) for x in xrange(33, 91)])
    salt = "".join([random.choice(chars) for x in xrange(10)])
    ctx = sha.new(password)
    ctx.update(salt)
    hash = "{SSHA}" + base64.b64encode(ctx.digest() + salt)
    return hash
