from comar.service import *
import os

serviceType = "local"
serviceDesc = "ACPID"

def check_config():
    if not os.path.exists("/proc/acpi"):
        fail("ACPI support has not been found")

def start():
    check_config()
    ret = run("/sbin/start-stop-daemon --start --quiet --exec /usr/sbin/acpid -- -c /etc/acpi/events")
    if ret == 0:
        notify("System.Service.changed", "started")

def stop():
    ret = run("/sbin/start-stop-daemon --stop --quiet --exec /usr/sbin/acpid")
    if ret == 0:
        notify("System.Service.changed", "stopped")

def reload():
    run("/sbin/start-stop-daemon --stop --quiet --exec /usr/sbin/acpid --signal HUP")
