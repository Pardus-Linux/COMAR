#!/usr/bin/python

import socket
import sys

s = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
s.connect("/tmp/comar")
s.send(sys.argv[1])
print s.recv(500)
s.close()
