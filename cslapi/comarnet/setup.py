
from distutils.core import setup, Extension

module1 = Extension('comarnet',
                    sources = ['comarnet.c'])

setup (name = 'COMAR Network',
       version = '0.1',
       description = 'Comar Network utilities',
       ext_modules = [module1])
