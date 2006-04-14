from comar.service import *
import os

serviceType = "local"
serviceDesc = "Zemberek Spell Checker"

def start():
    loadEnvironment()
    
    if not os.environ.has_key("JAVA_HOME"):
        fail("Where is Java?")
    javapath = os.environ["JAVA_HOME"]
    
    os.environ["LC_ALL"] = "tr_TR.UTF-8"
    os.chdir("/opt/zemberek-server")
    
    run("/sbin/start-stop-daemon -b --start --quiet --pidfile " +
        "/var/run/zemberek.pid --make-pidfile --exec %s/bin/java " % javapath +
        "-- -jar zemberek_server-0.3.jar"
    )

def stop():
    run("/sbin/start-stop-daemon", "--stop", "--quiet", "--pidfile", "/var/run/zemberek.pid")

def status():
    return checkDaemon("/var/run/zemberek.pid")
