#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

import sys
import os
import subprocess


class OpenGL:
    env_path = '/etc/env.d/03opengl'
    
    def __init__(self):
        self.fake = False
        self.impheaders = False
        self.current = self.getCurrent()
        self.available = self.getAvailable()
    
    # Low level operations
    def opUnlink(self, name):
        if self.fake:
            print "unlink(%s)" % name
        else:
            os.unlink(name)
    
    def opSymlink(self, src, dest):
        if self.fake:
            print "link(%s -> %s)" % (dest, src)
        else:
            os.symlink(src, dest)
    
    def opWrite(self, name, content):
        if self.fake:
            print "write(%s)" % name
        else:
            file(name, "w").write(content)
    
    def opUpdateEnv(self):
        if self.fake:
            print "update_environment()"
        else:
            subprocess.run(["/sbin/update-environment"])
    
    # Utilities
    def setLibrary(self, spath, dpath, name):
        for suffix in (".a", ".so", ".la"):
            self.setLibraryFile(spath, dpath, name + suffix)
    
    def setLibraryFile(self, spath, dpath, name):
        sname = os.path.join(spath, name)
        dname = os.path.join(dpath, name)
        if os.path.islink(dname):
            self.opUnlink(dname)
        if not os.path.exists(sname):
            return
        if name.endswith(".la"):
            data = file(sname).read()
            # FIXME: fix paths
            self.opWrite(dname, data)
        else:
            self.opSymlink(sname, dname)
    
    # Main methods
    def getAvailable(self):
        paths = ("/usr/lib/opengl",)
        # FIXME: lib32 and lib64 should be checked too for 64 bit support
        implems = []
        for path in paths:
            if os.path.exists(path):
                for name in os.listdir(path):
                    if os.path.isdir(os.path.join(path, name)) and name != "global":
                        implems.append(name)
        return implems
    
    def getCurrent(self):
        current = None
        dict = {}
        for line in file(self.env_path):
            if '=' in line:
                key, value = line.rstrip('\n').split('=')
                if value[0] == '"' or value[0] == "'":
                    value = value[1:-1]
                dict[key] = value
        current = dict.get("OPENGL_PROFILE", None)
        if not current:
            tmp = dict["LDPATH"]
            i = tmp.find("opengl/") + 7
            current = tmp[i:tmp.find("/", i)]
        return current
    
    def setCurrent(self, implem):
        # Setup libraries
        ipath = os.path.join("/usr/lib/opengl", implem)
        libpath = os.path.join(ipath, "lib")
        self.setLibrary(libpath, "/usr/lib", "libGL")
        self.setLibrary(libpath, "/usr/lib", "libGLcore")
        # Setup extensions
        extpath = os.path.join(ipath, "extensions")
        self.setLibrary(extpath, "/usr/lib/modules/extensions", "libglx")
        for name in os.listdir(extpath):
            if name.endswith(".so") or name.endswith(".a") or name.endswith(".la"):
                self.setLibraryFile(extpath, "/usr/lib/modules/extensions", name)
        # Setup includes
        # FIXME: really setup includes here
        # Setup environment
        data = 'LDPATH="%s"\nOPENGL_PROFILE="%s"\n' % (ipath, implem)
        self.opWrite(self.env_path, data)
        # Fixup links and environment
        self.opUpdateEnv()


def usage():
    o = OpenGL()
    
    print "Usage: update-opengl [OPTIONS] <GL-implementation>"
    print
    print "Options:"
    print "  --fake  Dont do anything, just show the operations"
    print
    print "Available implementations:\n  %s" % " ".join(o.available)

def main(args):
    if len(args) == 0:
        usage()
        sys.exit(0)
    
    if "--get-implementation" in args:
        o = OpenGL()
        print o.current
        sys.exit(0)
    
    o = OpenGL()
    
    if "--impl-headers" in args:
        args.remove("--impl-headers")
        o.impheaders = True
    
    if "--fake" in args:
        args.remove("--fake")
        o.fake = True
    
    o.setCurrent(args[0])

if __name__ == "__main__":
    main(sys.argv[1:])
