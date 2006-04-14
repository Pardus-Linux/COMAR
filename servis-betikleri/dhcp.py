import os
from comar.service import *

serviceType = "server"
serviceDesc = "DHCP Daemon"

def start():
    ret = run("start-stop-daemon --start --exec /usr/sbin/dhcpd --p /var/run/dhcp/dhcpd.pid -u dhcp -g dhcp eth0")
    if ret == 0:
        notify("System.Service.changed", "started")

def stop():
    ret = run("start-stop-daemon --stop --exec /usr/sbin/dhcpd --p /var/run/dhcp/dhcpd.pid")
    if ret == 0:
        notify("System.Service.changed", "stopped")

def status():
    return checkDeamon("/var/run/dhcp/dhcpd.pid")
