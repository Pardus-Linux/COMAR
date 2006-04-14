from comar.service import *
import os

serviceType = "server"
serviceDesc = "Powersave"

def start():
    call("System.Service.start", "hald")
    ret = run("/sbin/start-stop-daemon --start -q --exec /usr/sbin/powersaved -- -f /etc/acpi/events -d")
    if ret == 0:
        notify("System.Service.changed", "started")

def stop():
    ret = run("/sbin/start-stop-daemon --stop -q --exec /usr/sbin/powersaved")
    if ret == 0:
        notify("System.Service.changed", "stopped")
