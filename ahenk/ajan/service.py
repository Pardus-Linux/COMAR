from comar.service import *

serviceType = "local"
serviceDesc = _({"en": "Ahenk Agent",
                 "tr": "Ahenk Ajanı"})

def start():
    startService(command="/sbin/ahenk-ajan.py",
                 detach=True,
                 makepid=True,
                 pidfile="/var/run/ahenk-ajan.pid",
                 donotify=True)

def stop():
    stopService(pidfile="/var/run/ahenk-ajan.pid",
                signalno=1,
                donotify=True)

def status():
    return isServiceRunning("/var/run/ahenk-ajan.pid")
