# -*- coding: utf-8 -*-

import piksemel
import subprocess

def domodules(filepath):
    doc = piksemel.parse(filepath)
    for item in doc.tags("File"):
        path = item.getTagData("Path")
        if path.startswith("lib/modules/"):
            subprocess.call(["/sbin/update-modules"])
            return

def setupPackage(metapath, filepath):
    domodules(filepath)

def cleanupPackage(metapath, filepath):
    domodules(filepath)
