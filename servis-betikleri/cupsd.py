from comar.service import *

serviceType = "server"
serviceDesc = "CUPSD"

def start():
    call("System.Service.start", "hplip")
    ret = run("/sbin/start-stop-daemon --start -q --exec /usr/sbin/cupsd")
    if ret == 0:
        notify("System.Service.changed", "started")

def stop():
    ret = run("/sbin/start-stop-daemon --stop -q --exec /usr/sbin/cupsd")
    if ret == 0:
        notify("System.Service.changed", "stopped")

def status():
    return checkExecutable("/usr/sbin/cupsd")
