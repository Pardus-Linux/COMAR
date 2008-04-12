# -*- coding: utf-8 -*-

import os
import subprocess
import time
import sha

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
    try:
        if os.path.exists(_file):
            os.rename(_file, "%s-backup" % _file)
        return True
    except:
        return False

def getDate():
    return time.ctime()

def getChecksum(_data):
    return sha.sha(_data).hexdigest()

def getKernelOpt(cmdopt=None):
    if cmdopt:
        for cmd in "".join(loadFile("/proc/cmdline")).split():
            if cmd.startswith("%s=" % cmdopt):
                return cmd[len(cmdopt)+1:].split(",")
    else:
        return "".join(loadFile("/proc/cmdline")).split()

    return ""

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

def xisrunning():
    return os.path.exists(xorg_lock)

def parseMode(mode):
    m = mode.split("-", 1)
    res = m.pop(0)

    try:
        w, h = map(int, res.split("x", 1))
    except:
        return None, None

    depth = None

    if m:
        try:
            d = int(m[0])
            if d in (16, 24):
                depth = d
            else:
                res = None
        except ValueError:
            res = None

    return res, depth

