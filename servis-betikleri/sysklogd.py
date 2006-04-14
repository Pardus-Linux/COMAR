from comar.service import *
import os
import time

serviceType = "server"
serviceDesc = "System Logger"

def start():
    ret1 = run("start-stop-daemon --start --quiet --background --exec /usr/sbin/syslogd -- -m 15")

    # klogd do not always start proper if started too early
    time.sleep(1)
    ret2 = run("start-stop-daemon --start --quiet --background --exec /usr/sbin/klogd -- -c 3 -2")
    if ret1 == 0 and ret2 == 0:
        notify("System.Service.changed", "started")
            
def stop():
    ret1 = run("start-stop-daemon --stop --oknodo --retry 15 --quiet --pidfile /var/run/klogd.pid")
    ret2 = run("start-stop-daemon --stop --oknodo --retry 15 --quiet --pidfile /var/run/syslogd.pid")
    if ret1 == 0 and ret2 == 0:
        notify("System.Service.changed", "stopped")

def status():
    return checkDaemon("/var/run/syslogd.pid")
