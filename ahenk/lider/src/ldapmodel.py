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
        self.fields = {}
        self.options = {}
        self.widgets = []
        self.append = {}
        self.fromEntry(attr)
    
    def fromEntry(self, attr):
        """ 'entries' is a tuple of tuples in format varname, attrname, valuetype and  append_values values respectively
            fromEntry  reads attribute names , makes necessary format casts and stores in LDapClass' 'varname' attribute 
        """
        for varname, attrname, valuetype, append_values, label, widget, options in self.entries:
            value = attr.get(attrname, None)
            if valuetype == int:
                if value:
                    val = int(value[0])
                else:
                    val = 0
            elif valuetype == str:
                if value:
                    val = str(value[0])
                else:
                    val = ""
            elif valuetype == set:
                if value:
                    val = set(value)
                else:
                    val = set()
            elif valuetype == list:
                if value:
                    val = value
                else:
                    val = []
            self.widgets.append((varname, label, widget,))
            self.options[varname] = options
            self.fields[varname] = val
            self.append[varname] = append_values
    
    def toEntry(self, exclude=[], include=[], append=False):
        """  Reads attributes from entries to a list'attr' 
             If the attribute type is int type conversion is made to str    
        """
        attr = {}
        for item in self.entries:
            if item[0] in exclude:
                continue
            elif include and item[0] not in include:
                continue
            val = self.fields[item[0]]
            if item[2] == int:
                val = str(val)
            elif item[2] == set:
                val = list(val)
            if item[2] in [list, set] and append:
                for i in self.append.get(item[0], []):
                    if i not in val:
                        val.append(i)
            attr[item[1]] = val
        return attr
    
    def __str__(self):
        """ overrides method -str() cast- for 'entries's tuples to become a string in wanted format"""
        text = []
        for varname, attrname, valuetype, append_values, label, widget, options in self.entries:
            value = getattr(self, varname, "")
            text.append("%s: %s" % (attrname, value))
        return "\n".join(text)
