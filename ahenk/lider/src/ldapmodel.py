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
    allow_multiple_edit = False
    
    def __init__(self, attr={}):
        self.fields = {}
        self.options = {}
        self.widgets = []
        self.groups = {}
        self.new = True
        self.fromEntry(attr)
    
    def fromEntry(self, attr):
        """ 'entries' is a tuple of tuples in format varname, attrname, valuetype and  append_values values respectively
            fromEntry  reads attribute names , makes necessary format casts and stores in LDapClass' 'varname' attribute 
        """
        for varname, attrname, valuetype, label, widget, group, options in self.entries:
            value = attr.get(attrname, None)
            if value:
                self.new = False
            if valuetype == int:
                if value:
                    val = int(value[0])
                else:
                    val = []
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
    
    def toEntry(self, multiple=False):
        """  Reads attributes from entries to a list'attr' 
             If the attribute type is int type conversion is made to str    
        """
        attr = {}
        for item in self.entries:
            val = self.fields[item[0]]
            if val:
                if item[2] == int:
                    if not isinstance(val, list):
                        val = str(val)
                elif item[2] == set:
                    val = list(val)
                attr[item[1]] = val
            else:
                attr[item[1]] = []
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
