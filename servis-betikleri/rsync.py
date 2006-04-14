import os
from comar.service import *

serviceType = "server"
serviceDesc = "Rsync Daemon"

def start():
    run("rsync --daemon")

def stop():
    run("/sbin/start-stop-daemon --stop --pidfile /var/run/rsyncd.pid")

def status():
    return checkDaemon("/var/run/rsyncd.pid")
