import os
from comar.service import *

serviceType = "local"
serviceDesc = "Portmap"

def start():
    run("/sbin/portmap")

def stop():
    run("start-stop-daemon --stop --exec /sbin/portmap")
