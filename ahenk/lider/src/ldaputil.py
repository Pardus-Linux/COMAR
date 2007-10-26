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
    
    name = ""
    name_field = ""
    object_label = ""
    objectClass = []
    entries = ()
    
    def __init__(self, attr={}, connection=None):
        self.fields = {}
        self.options = {}
        self.widgets = []
        self.groups = {}
        self.new = True
        self.connection = connection
        self.fromEntry(attr)
    
    def fromEntry(self, attr):
        """ 'entries' is a tuple of tuples in format varname, attrname, valuetype and  append_values values respectively
            fromEntry  reads attribute names , makes necessary format casts and stores in LDapClass' 'varname' attribute 
        """
        for varname, attrname, valuetype, label, widget, group, options in self.entries:
            value = attr.get(attrname, None)
            if value is not None:
                self.new = False
                if valuetype == int:
                    val = int(value[0])
                elif valuetype == str:
                    val = str(value[0])
                elif valuetype == set:
                    val = set(value)
                else:
                    val = value
            else:
                if valuetype == str:
                    val = ""
                elif valuetype == set:
                    val = set()
                else:
                    val = []
            
            if self.name_field in attr:
                self.name = attr[self.name_field][0]
            else:
                self.name = ""
            self.widgets.append((varname, label, widget,))
            self.options[varname] = options
            self.fields[varname] = val
            if widget and group:
                if group not in self.groups:
                    self.groups[group] = []
                self.groups[group].append(varname)
    
    def toEntry(self, multiple=False, only_fields=[]):
        """  Reads attributes from entries to a list'attr' 
             If the attribute type is int type conversion is made to str    
        """
        attr = {}
        for varname, attrname, valuetype, label, widget, group, options in self.entries:
            if varname not in self.fields:
                continue
            if len(only_fields) and varname not in only_fields:
                continue
            val = self.fields[varname]
            if val is not None:
                if valuetype == int:
                    if not isinstance(val, list):
                        val = str(val)
                elif valuetype == set:
                    val = list(val)
                elif valuetype == str:
                    if isinstance(val, list):
                        sep = options.get("item_seperator", ",")
                        val = sep.join(val)
                attr[attrname] = val
            else:
                attr[attrname] = []
            attr["objectClass"] = self.objectClass
            if self.name and not multiple:
                attr[self.name_field] = self.name
        return attr
    
    def __str__(self):
        """ overrides method -str() cast- for 'entries's tuples to become a string in wanted format"""
        text = []
        for varname, attrname, valuetype, label, widget, group, options in self.entries:
            value = getattr(self, varname, "")
            text.append("%s: %s" % (attrname, value))
        return "\n".join(text)
