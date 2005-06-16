#!/usr/bin/python

import socket
import sys

s = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
s.connect("/tmp/comar")
s.send(sys.argv[1])
s.close()
