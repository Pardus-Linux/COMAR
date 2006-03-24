import os
from comar.service import *

serviceType = "server"
serviceDesc = "Apache Web Server"

def start():
    run("/usr/sbin/apachec2tl", "start")

def stop():
    run("/usr/sbin/apachec2tl", "stop")

