#!/usr/bin/python
# -*- coding: utf-8 -*-

from distutils.core import setup
from distutils.command.install import install
from distutils.cmd import Command

import glob
import os
import shutil
import sys

import kdedistutils

version = "0.2"

distfiles = """
    setup.py
    src/*.py
    src/*.png
    po/*.po
    po/*.pot
    *.desktop
    AUTHORS
    COPYING
    README
"""

def make_dist():
    distdir = "lider-%s" % version
    list = []
    for t in distfiles.split():
        list.extend(glob.glob(t))
    if os.path.exists(distdir):
        shutil.rmtree(distdir)
    os.mkdir(distdir)
    for file_ in list:
        cum = distdir[:]
        for d in os.path.dirname(file_).split('/'):
            dn = os.path.join(cum, d)
            cum = dn[:]
            if not os.path.exists(dn):
                os.mkdir(dn)
        shutil.copy(file_, os.path.join(distdir, file_))
    os.popen("tar -cjf %s %s" % ("lider-" + version + ".tar.bz2", distdir))
    shutil.rmtree(distdir)

if "dist" in sys.argv:
    make_dist()
    sys.exit(0)

kdedistutils.setup(
    name="lider",
    version=version,
    author="Bahadır Kandemir",
    author_email="bahadir@pardus.org.tr",
    min_kde_version = "3.5.0",
    min_qt_version = "3.3.5",
    license = "GPL",
    application_data = ["src/browser.py", "src/dialogs.py", "src/domain.py", "src/lider.py",
                        "src/mainwindow.py", "src/utility.py", "src/ldapmodel.py", "src/ldapview.py",
                        "src/ldaputil.py",
                        ('/usr/kde/3.5/share/applications/kde/', ['lider.desktop']),
                        ("/usr/kde/3.5/share/icons/hicolor/128x128/apps", ["src/lider.png"])],
    executable_links = [("lider", "lider.py")],
    i18n = ("po", ["src/"]),
    )
