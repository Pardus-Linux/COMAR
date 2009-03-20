# -*- coding: utf-8 -*-

import os
import subprocess

from pardus.sysutils import get_kernel_option

xorg_lock = "/tmp/.X0-lock"

def atoi(s):
    # python's int() borks when given non integer characters
    t = ""
    for c in s.lstrip():
        if c in "0123456789":
            t += c
        else:
            break
    try:
        ret = int(t)
    except:
        ret = 0
    return ret

def unlink(path):
    try:
        os.unlink(path)
    except:
        pass

def touch(_file):
    try:
        if not os.path.exists(_file):
            file(_file, "w").close()
    except:
        pass

def backup(_file):
    def rename_backup(src, n):
        if n == 4:
            return

        new_name = "%s-backup%d" % (_file, n)
        if os.path.exists(new_name):
            rename_backup(new_name, n+1)

        try:
            os.rename(src, new_name)
        except IOError:
            pass


    if os.path.exists(_file):
        backup_file = "%s-backup" % _file
        if os.path.exists(backup_file):
            rename_backup(backup_file, 2)
        try:
            os.rename(_file, backup_file)
        except IOError:
            pass

def capture(*cmd):
    a = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return a.communicate()

def run(*cmd):
    f = file("/dev/null", "w")
    return subprocess.call(cmd, stdout=f, stderr=f)

def loadFile(_file):
    try:
        f = file(_file)
        d = [a.strip() for a in f]
        d = (x for x in d if x and x[0] != "#")
        f.close()
        return d
    except:
        return []

def lremove(str, pre):
    if str.startswith(pre):
        return str[len(pre):]
    return str

def sysValue(path, dir, _file):
    f = file(os.path.join(path, dir, _file))
    data = f.read().rstrip('\n')
    f.close()
    return data

def idsQuery(vendor, device, idsFile="/usr/share/misc/pci.ids"):
    f = file(idsFile)
    flag = 0
    company = "Unknown Company"
    model = "Unknown Model"

    for line in f.readlines():
        if flag == 0:
            if line.startswith(vendor):
                flag = 1
                company = line[5:].strip()
        else:
            if line.startswith("\t"):
                if line.startswith("\t" + device):
                    model = line[6:].strip()
                    break
            elif not line.startswith("#"):
                flag = 0

    return company, model

def xisrunning():
    return os.path.exists(xorg_lock)

def isVirtual():
    # Xen detection
    if os.path.exists("/proc/xen/capabilities"):
        # we are in dom0, act like normal system
        if loadFile("/proc/xen/capabilities") == []:
            # and in domU, configure X to use fbdev if exists
            return True
    return False

def jailEnabled():
    xorg_options = get_kernel_option("xorg")

    if not "nojail" in xorg_options:
        if "thin" in get_kernel_option("mudur") or "jail" in xorg_options:
            print "Jail is enabled"
            return True
    return False
