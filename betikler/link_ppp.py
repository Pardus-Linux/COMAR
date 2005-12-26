#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import os
import popen2
from csapi import atoi
from signal import SIGTERM


class Dialup:
    """ Dialup client functions for Hayes compatible modems, using pppd """

    tmpl_chat = """
TIMEOUT         5
ABORT           '\\nBUSY\\r'
ABORT           '\\nNO ANSWER\\r'
ABORT           '\\nNO CARRIER\\r'
ABORT           '\\nNO DIALTONE\\r'
ABORT           '\\nAccess denied\\r'
ABORT           '\\nInvalid\\r'
ABORT           '\\nVOICE\\r'
ABORT           '\\nRINGING\\r\\n\\r\\nRINGING\\r'
''              \\rAT
'OK-+++\c-OK'   ATH0
TIMEOUT         30
OK              ATL%s
OK              ATDT%s
CONNECT         ''
"""
    
    tmpl_options = """
lock
modem
crtscts
noipdefault
defaultroute
noauth
usehostname
usepeerdns
linkname %s
user %s
%s
"""

    def silentUnlink(self, path):
        """ Try to unlink a file, if exists """

        try:
            os.unlink(path)
        except:
            pass

    def capture(self, cmd):
        """ Run a command and capture the output """

        out = []
        a = popen2.Popen4(cmd)
        while 1:
            b = a.fromchild.readline()
            if b == None or b == "":
                break
            out.append(b)
        return (a.wait(), out)

    def sendCmd(self, cmd, dev):
        """ Send commands to dev """

        return result

    def isModem(self, dev):
        """ Check if dev is a modem """
        
        return True

    def getDNS(self):
        """ Try to get DNS server adress provided by remote peer """

        list = []
        try:
            f = file("/etc/ppp/resolv.conf", "r")
            for line in f.readlines():
                if line.strip().startswith("nameserver"):
                    list.append(line[line.find("nameserver") + 10:].rstrip('\n').strip())
            f.close()
        except IOError:
            return None

        return list

    def createOptions(self, dev, user, speed):
        """ Create options file for the desired device """

        self.silentUnlink("/etc/ppp/options." + dev)
        try:
            f = open("/etc/ppp/options." + dev, "w")
            f.write(self.tmpl_options % (dev, user, speed))
            f.close()
        except:
            return True

        return None

    def createChatscript(self, dev, phone, vol):
        """ Create a script to have a chat with the modem in the frame of respect and love """

        self.silentUnlink("/etc/ppp/chatscript." + dev)
        try:
            f = open("/etc/ppp/chatscript." + dev, "w")
            f.write(self.tmpl_chat % (vol, phone))
            f.close()
        except:
            return True

        return None


    def createSecrets(self, user, pwd):
        """ Create authentication files """

        try:
            # Ugly way to clean up secrets and recreate
            self.silentUnlink("/etc/ppp/pap-secrets")
            self.silentUnlink("/etc/ppp/chap-secrets")
            f = os.open("/etc/ppp/pap-secrets", os.O_CREAT, 0600)
            os.close(f)
            os.symlink("/etc/ppp/pap-secrets", "/etc/ppp/chap-secrets")
        except:
            return True
            
        f = open("/etc/ppp/pap-secrets", "w")
        data = "\"%s\" * \"%s\"\n" % (user, pwd)
        f.write(data)
        f.close()

        return None

    def stopPPPD(self, dev):
        """ Stop the connection and hangup the modem """

        try:
            f = open("/var/lock/LCK.." + dev, "r")
            pid = atoi(f.readline())
            f.close()
        except:
            return "Could not open lockfile"

        try:
            os.kill(pid, SIGTERM)
        except OSError:
            return "Could not stop the process"

        return "Killed"

    def runPPPD(self, dev):
        """ Run the PPP daemon """

        # PPPD does some isatty and ttyname checks, so we shall satisfy it for symlinks and softmodems
        cmd = "/usr/sbin/pppd /dev/" + dev + " connect '/usr/sbin/chat -V -v -f /etc/ppp/chatscript." + dev + "'"
        i, output = self.capture(cmd)

        return output

    def dial(self, phone, user, pwd, speed, vol, modem = "modem"):
        """ Dial a server and try to login """
    
        dev = modem.lstrip("/dev/")

        if self.createSecrets(user, pwd) is True:
            return "Could not manage authentication files"

        if self.createOptions(dev, user, speed) is True:
            return "Could not manage pppd parameters"

        if self.createChatscript(dev, phone, vol) is True:
            return "Could not manage chat script"

        output = self.runPPPD(dev)
        return output


def _device_dev(uid):
    return uid[uid.find(":") + 1:]

def _device_info(uid):
    return "COM %d" % (atoi(uid[uid.find("S") + 1:]) + 1)

def _get(dict, key, default):
    val = default
    if dict and dict.has_key(key):
        val = dict[key]
    return val


class Dev:
    def __init__(self, name):
        dict = get_instance("name", name)
        self.uid = _get(dict, "device", None)
        self.name = name
        self.dev = None
        if self.uid:
            self.dev = _device_dev(self.uid)
        self.uid = _get(dict, "remote", None)
        self.state = _get(dict, "state", "down")
        self.user = _get(dict, "user", None)
        self.password = _get(dict, "password", None)
    
    def up(self):
        dial = Dialup()
        
        if self.remote and self.user and self.password and self.dev:
            notify("Net.Link.stateChanged", self.name + "\nconnecting")
            
            dial.dial(self.remote, self.user, self.password, "115200", "1", self.dev)
            
            notify("Net.Link.stateChanged", self.name + "\nup")
    
    def down(self):
        dial = Dialup()
        dial.stopPPPD(self.dev)
        notify("Net.Link.stateChanged", self.name + "\ndown")


# lala

sysfs_path = "/sys/devices/platform/serial8250"

def modes():
    return "device,remote,loginauth"

def linkInfo():
    return "\n".join([
        "dialup",
        "Dialup network",
        "Phone number"
    ])

def deviceList():
    iflist = []
    for iface in os.listdir(sysfs_path):
        if iface.startswith("tty:"):
            iflist.append("%s %s" % (iface, _device_info(iface)))
    return "\n".join(iflist)

def scanRemote():
    fail("Not supported")

def setConnection(name=None, device=None):
    dict = get_instance("name", name)
    if dict and dict.has_key("device"):
        notify("Net.Link.connectionChanged", "configured device " + name)
    else:
        notify("Net.Link.connectionChanged", "added " + name)

def deleteConnection(name=None):
    dev = Dev(name)
    if dev.dev and dev.state == "up":
        dev.down()
    notify("Net.Link.connectionChanged", "deleted " + name)

def setAddress(name=None, mode=None, address=None, mask=None, gateway=None):
    fail("Not supported")

def setRemote(name=None, remote=None):
    pass

def setAuthentication(name=None, mode=None, user=None, password=None, key=None):
    pass

def setState(name=None, state=None):
    dev = Dev(name)
    if state != "up" and state != "down":
        fail("Unknown state")
    
    notify("Net.Link.connectionChanged", "configured state " + name)
    
    if not dev.dev:
        fail("Device not found")
    
    if state == "up":
        dev.up()
    else:
        if dev.state == "up":
            dev.down()

def connections():
    list = instances("name")
    if list:
        return "\n".join(list)
    return ""

def connectionInfo(name=None):
    dict = get_instance("name", name)
    if not dict:
        fail("No such connection")
    s = "\n".join([name, dict["device"], _device_info(dict["device"])])
    return s

def getAddress(name=None):
    fail("Not supported")

def getRemote(name=None):
    dev = Dev(name)
    return name + "\n" + dev.remote

def getAuthentication(name=None):
    dev = Dev(name)
    return "%s\nlogin\n%s\n%s" % (name, dev.user, dev.password)

def getState(name=None):
    dev = Dev(name)
    if not dev:
        fail("No such connection")
    return name + "\n" + dev.state
