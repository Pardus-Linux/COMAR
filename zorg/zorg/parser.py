# -*- coding: utf-8 -*-

trueList = ("1", "on", "true", "yes", "enable")
falseList = ("0", "off", "false", "no", "disable")

xBool = {True: "true", False: "false"}

class unquoted(str):
    pass

class XorgEntry:
    def __init__(self, line = ""):
        line = line.strip()
        if line == "":
            self.key = ""
            self.values = []
            return

        v = line.split(None, 1)
        self.key = v.pop(0)
        if v:
            line = v[0].strip()
        else:
            line = ""

        self.values = []
        while line:
            if line[0] == '"':
                end = line.index('"', 1)
                self.values.append(line[1:end])
                line = line[end+1:].lstrip()
            elif line[0] == "#":
                break
            else:
                v = line.split(None, 1)
                arg = v.pop(0)
                if v:
                    line = v[0].strip()
                else:
                    line = ""

                if arg[0] == "0" and len(arg) > 1:
                    self.values.append(unquoted(arg))
                else:
                    try:
                        self.values.append(int(arg))
                    except ValueError:
                        self.values.append(unquoted(arg))

    def __str__(self):
        s = "%s\t%s" % (self.key, entryFormat(self.values))
        return s

    def __repr__(self):
        return "<XorgEntry: %s>" % str(self)

def entryFormat(values):
    s = ""
    for v in values:
        if isinstance(v, basestring) and not isinstance(v, unquoted):
            s += ' "%s"' % v
        else:
            s += " %s" % v

    return s.lstrip()

class XorgSection:
    def __init__(self, name):
        self.name = name
        self.sections = []
        self.entries = []
        self.options = {}

    def entry(self, key):
        key = key.lower()
        for entry in self.entries:
            if entry.key.lower() == key:
                return entry
        return None

    def __repr__(self):
        return "<XorgSection '%s'>" % self.name

    def getEntries(self, key):
        return tuple(x for x in self.entries if x.key == key)

    def getSections(self, *names):
        return tuple(x for x in self.sections if x.name in names)

    def get(self, key, index = 0, default = None):
        entry = self.entry(key)
        if entry:
            return entry.values[index]
        else:
            return default

    def set(self, key, *values):
        entry = self.entry(key)
        if entry:
            entry.values = values
        else:
            self.add(key, *values)

    def add(self, key, *values):
        entry = XorgEntry(key)
        entry.values = values
        self.entries.append(entry)

class XorgParser:
    def __init__(self):
        self.sections = []

    def parseFile(self, filePath):
        section = None
        stack = [self]

        lines = file(filePath).readlines()
        for line in lines:
            e = XorgEntry(line)
            key = e.key.lower()

            if key == "" or key[0] == "#":
                continue

            elif key in ("section", "subsection"):
                section = XorgSection(e.values[0])
                stack[-1].sections.append(section)
                stack.append(section)

            elif section:
                if key in ("endsection", "endsubsection"):
                    stack.pop()
                    if stack:
                        section = stack[-1]
                    else:
                        section = None

                elif e.values and key == "option":
                    key = e.values.pop(0)
                    if e.values:
                        value = e.values[0]
                    else:
                        value = "true"

                    section.options[key] = value

                else:
                    section.entries.append(e)

    def getSections(self, *names):
        secs = tuple(x for x in self.sections if x.name in names)
        #return secs
        if secs:
            return secs
        else:
            secs = []
            for name in names:
                sec = XorgSection(name)
                secs.append(sec)
                self.sections.append(sec)
            return secs # :)

    def toString(self):
        s = ""

        def writeSection(sect, dep):
            s = '%sSubSection "%s"\n' % ("\t" * dep, sect.name)

            # Entries except 'Option'
            for e in sect.entries:
                s += "%s%s\t%s\n" % ("\t" * (dep+1), e.key, entryFormat(e.values))

            # Options
            for k, v in sect.options.items():
                ent = XorgEntry('Option "%s"' % k)
                ent.values.append(v)
                s += "%s%s\n" % ("\t" * (dep+1), ent)

            # Sub sections
            for sec in sect.sections:
                s += writeSection(sec, dep + 1)
            s += "%sEndSubSection\n" % "\t" * dep
            return s

        for section in self.sections:
            s += 'Section "%s"\n' % section.name

            for e in section.entries:
                s += "\t%s\t%s\n" % (e.key, entryFormat(e.values))

            for k, v in section.options.items():
                ent = XorgEntry('Option "%s"' % k)
                ent.values.append(v)
                s += "\t%s\n" % ent

            for sec in section.sections:
                s += writeSection(sec, 1)

            s += "EndSection\n\n"

        return s.expandtabs(4)
