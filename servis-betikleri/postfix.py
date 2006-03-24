import os
from comar.service import *

serviceType = "server"
serviceDesc = "Postfix Mail Server"

def start():
    run("/usr/sbin/postfix", "start")

def stop():
    run("/usr/sbin/postfix", "stop")

