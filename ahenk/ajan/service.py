from comar.service import *
from comar.utility import FileLock

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
    alock = FileLock("/var/run/.ahenk.lock")
    alock.lock()
    stopService(pidfile="/var/run/ahenk-ajan.pid",
                donotify=True)
    alock.unlock()

def status():
    return isServiceRunning("/var/run/ahenk-ajan.pid")
