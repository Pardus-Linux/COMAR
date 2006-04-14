import os
from comar.service import *

serviceType = "server"
serviceDesc = "Apache Web Server"

def start():
    ret = run("/usr/sbin/apache2ctl", "-d", "/usr/lib/apache2/", "-f", "/etc/apache2/httpd.conf", get_config_vars(), "-k", "start")
    if ret == 0:
        notify("System.Service.changed", "started")

def stop():
    ret = run("/usr/sbin/apache2ctl", "-d", "/usr/lib/apache2/", "-f", "/etc/apache2/httpd.conf", get_config_vars(), "-k", "stop")
    if ret == 0:
        notify("System.Service.changed", "stopped")

def reload():
    run("/usr/sbin/apache2ctl", "-d", "/usr/lib/apache2/", "-f", "/etc/apache2/httpd.conf", get_config_vars(), "-k", "graceful")

def status():
    return checkDaemon("/var/run/apache2.pid")

def get_config_vars():
    return map(lambda x: x.split('=')[1].strip().strip('"'), [line for line in open('/etc/conf.d/apache2').readlines() if line.strip().startswith('APACHE2_OPTS')])[0]
