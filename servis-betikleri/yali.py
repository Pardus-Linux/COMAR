from comar.service import *
import os

serviceType = "script"
serviceDesc = "Yet Another Linux Installer"
serviceDefault = "on"

def configure():
    if not os.path.exists("/etc/X11/xorg.conf"):
        run("/sbin/xorg.py")

def start():
    call("System.Service.start", "acpid")
    call("System.Service.start", "dbus")
    configure()
    loadEnvironment()
    os.environ["XAUTHLOCALHOSTNAME"]=os.uname()[1]
    os.environ["HOME"]="/root"
    os.environ["USER"]="root"
    # if 0 == run("/usr/bin/xinit /usr/bin/yali-bin -- tty6 vt7 -nolisten tcp -br"):
    if 0 == run("/usr/bin/xinit /usr/bin/yali-bin -- vt7 -nolisten tcp -br"):
        notify("System.Service.changed", "started")

def stop():
    notify("System.Service.changed", "stopped")
