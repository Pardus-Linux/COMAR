import os
from comar.service import *

serviceType = "server"
serviceDesc = "DHCP Daemon"

def start():
    run("start-stop-daemon --start --exec /usr/sbin/dhcpd --p /var/run/dhcp/dhcpd.pid -u dhcp -g dhcp eth0")

def stop():
    run("start-stop-daemon --stop --exec /usr/sbin/dhcpd --p /var/run/dhcp/dhcpd.pid")

def status():
    return checkDeamon("/var/run/dhcp/dhcpd.pid")
