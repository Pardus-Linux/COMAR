import os
from comar.service import *

serviceType = "server"
serviceDesc = "NFS Daemon"

def start():
    run("/usr/sbin/exportfs -r")
    run("start-stop-daemon --start --quite --exec /sbin/rpc.statd")
    run("start-stop-daemon --start --quite --exec /usr/sbin/rpc.rquotad")
    run("start-stop-daemon --start --quite --exec /usr/sbin/rpc.nfsd")
    run("start-stop-daemon --start --quite --exec /usr/sbin/rpc.mountd")

def stop():
    run("start-stop-daemon --stop --exec /usr/sbin/dhcpd --p /var/run/dhcp/dhcpd.pid")
