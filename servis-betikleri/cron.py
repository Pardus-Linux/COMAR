from comar.service import *

serviceType = "local"
serviceDesc = "Cron"

def start():
    ret = run("start-stop-daemon --start --quiet --exec /usr/sbin/cron")
    if ret == 0:
        notify("System.Service.changed", "started")

def stop():
    ret = run("start-stop-daemon --stop --quiet --pidfile /var/run/cron.pid")
    if ret == 0:
        notify("System.Service.changed", "stopped")

def status():
    return checkDeamon("/var/run/cron.pid")
