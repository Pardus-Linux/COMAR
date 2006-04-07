import os
from comar.service import *

serviceType = "server"
serviceDesc = "TFTP Daemon"

def start():
    run("/usr/sbin/in.tftpd -s -l /tftpboot")

def stop():
    run("start-stop-daemon --stop --exec /usr/sbin/in.tftpd")
