from comar.service import *

serviceType = "local"
serviceDesc = "HP Printer/Scanner Services"

def start():
    ret1 = run("start-stop-daemon --start --quiet --exec /usr/sbin/hpiod")
    ret2 = run('start-stop-daemon --quiet --start --exec /usr/share/hplip/hpssd.py --pidfile /var/run/hpssd.pid')
    if ret1 == 0 and ret2 == 0:
        notify("System.Service.changed", "started")

def stop():
    ret1 = run("start-stop-daemon --stop --quiet -n hpiod")
    ret2 = run("start-stop-daemon --stop --pidfile /var/run/hpssd.pid")
    if ret1 == 0 and ret2 == 0:
        notify("System.Service.changed", "stopped")

def status():
    return checkDeamon("/var/run/hpssd.pid")
