#!/usr/bin/python

from distutils.core import setup
from distutils.core import Extension

ext = Extension("csapi", [ "csapi.c" ])

setup(name="csapi",
    version= "1.0",
    description="COMAR Script API",
    author="Pardus Developers",
    ext_modules = [ ext ],
    )
