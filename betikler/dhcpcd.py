#!/usr/bin/python
# -*- coding: utf-8 -*-

import popen2
from glob import glob

class dhcpc:
    def _run(self, args):
        cmd = "/sbin/dhcpcd " + args
        a = popen2.Popen4(cmd)

        return a.wait() 

    def start(self, ifname, timeout = "30"):
        """ Start the DHCP client daemon """
        # Maybe we should leave this to GUI
        if ifname in self.getRunning():
            self.stop(ifname)

        # -R -Y -N to prevent dhcpcd rewrite nameservers
        #          we should add nameservers, not rewrite them
        # -H to set hostname due to info from server
        # -t for timeout

        args = "-R -Y -N -H -t " + timeout + " " + ifname
        return self._run(args)

    def stop(self, ifname):
        """ Stop DHCP client daemon """
        args = "-k " + ifname
        return self._run(args)

    def getNameServers(self, ifname):
        """ Get DNS server list provided by the server """
        info_file = "/var/lib/dhcpc/dhcpcd-" + ifname + ".info"

        try:
            f = file(info_file)
            for line in f.readlines():
                if not line.find("DNS="):
                    return line[line.find("DNS=")+4:].rstrip('\n').split(',')
            f.close
        except IOError:
            return "Could not open file" # FIXME: put an error message here

    def getRunning(self):
        d = []
        for i in glob("/var/run/dhcpcd-*.pid"):
            d.append(i.rstrip(".pid").lstrip("/var/run/dhcpcd-"))
        return d

if __name__ == "__main__":
    dc = dhcpc()
    print "Daemons are running for", "".join(dc.getRunning())

