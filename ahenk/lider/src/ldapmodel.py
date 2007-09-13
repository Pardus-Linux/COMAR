#
# Copyright (C) 2007, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

class LdapClass:
    """ Designed for Ldap format for entries of modules of ajan """
    
    def __init__(self, attr={}):
        self.fromEntry(attr)
    
    def fromEntry(self, attr):
        """ 'entries' is a tuple of tuples in format varname, attrname, valuetype and  default values respectively
            fromEntry  reads attribute names , makes necessary format casts and stores in LDapClass' 'varname' attribute 
        """
        for varname, attrname, valuetype, default in self.entries:
            value = attr.get(attrname, None)
            if value:
                if valuetype == int:
                    val = int(value[0])
                elif valuetype == str:
                    val = unicode(value[0])
                elif valuetype == set:
                    val = set(value)
                else:
                    val = value
            else:
                val = default
            setattr(self, varname, val)
    
    def toEntry(self):
        """  Reads attributes from entries to a list'attr' 
             If the attribute type is int type conversion is made to str    
        """
        attr = {}
        for item in self.entries:
            val = getattr(self, item[0])
            if item[2] == int:
                val = [str(val)]
            elif item[2] == str:
                val = [val]
            elif item[2] == set:
                val = list(val)
            attr[item[1]] = val
        return attr
    
    def __str__(self):
        """ overrides method -str() cast- for 'entries's tuples to become a string in wanted format"""
        text = []
        for varname, attrname, valuetype, default in self.entries:
            value = getattr(self, varname, "")
            text.append("%s: %s" % (attrname, value))
        return "\n".join(text)
