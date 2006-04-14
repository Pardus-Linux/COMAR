import os
from comar.service import *

serviceType = "server"
serviceDesc = "Rsync Daemon"

def start():
    ret = run("rsync --daemon")
    if ret == 0:
        notify("System.Service.changed", "started")

def stop():
    ret = run("/sbin/start-stop-daemon --stop --pidfile /var/run/rsyncd.pid")
    if ret == 0:
        notify("System.Service.changed", "stopped")

def status():
    return checkDaemon("/var/run/rsyncd.pid")
