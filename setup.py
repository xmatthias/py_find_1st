#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

from setuptools import setup
#from distutils.core import setup
from distutils.extension import Extension
from distutils.command.build_ext import build_ext
from distutils.command.sdist import sdist 
import hashlib
import io
from pkg_resources import parse_version

import numpy as np
import os
import sys
import re
import subprocess

def utf8_to_bytes(ss):
    try:
        return bytes(ss, encoding="UTF-8")
    except TypeError :
        return bytes(ss)


def compiler_is_clang(comp) :
    print("check for clang compiler ...", end=' ')
    try:
        cc_output = subprocess.check_output(comp+['--version'],
                                           stderr = subprocess.STDOUT, shell=False)
    except OSError as ex:
        print("compiler test call failed with error {0:d} msg: {1}".format(ex.errno, ex.strerror))
        print("no")
        return False

    ret = re.search(b'clang', cc_output) is not None
    if ret :
        print("yes")
    else:
        print("no")
    return ret


class build_ext_subclass( build_ext ):
    def build_extensions(self):
        #c = self.compiler.compiler_type
        #print "compiler attr", self.compiler.__dict__
        #print "compiler", self.compiler.compiler
        #print "compiler is",c
        try:
            if compiler_is_clang(self.compiler.compiler):
                for e in self.extensions:
                    #e.extra_compile_args.append('-stdlib=libc++')
                    e.extra_compile_args.append('-Wno-unused-function')
                #for e in self.extensions:
                #    e.extra_link_args.append('-stdlib=libc++')
        except AttributeError:
            pass
        build_ext.build_extensions(self)

                
find_1st_ext = Extension("find_1st", ["utils_find_1st/find_1st.cpp"],
                         include_dirs=[np.get_include()],
                         language="c++",
                         define_macros = [("NPY_NO_DEPRECATED_API", "NPY_1_13_API_VERSION") ])

ext_modules=[find_1st_ext]

with open('./requirements.txt') as f:
    install_requires = [line.strip('\n') for line in f.readlines()]

# get _pysndfile version number
for line in open("utils_find_1st/__init__.py") :
    if "version" in line:
        version = re.split('[()]', line)[1].replace(',','.').replace(',','-',1).replace('"','').replace(' ','')
        break

if sys.argv[1] == "get_version":
    print(parse_version(version))
    sys.exit(0)

README_path       = os.path.join(os.path.dirname(__file__), 'README.md')
README_cksum_path = os.path.join(os.path.dirname(__file__), 'README.md.cksum')    

def write_readme_checksum(rdlen, rdsum):
    with open(README_cksum_path, "w") as fi:
        print("{} {}".format(rdlen, rdsum), file=fi)

def read_readme_checksum():
    try:
        with open(README_cksum_path, "r") as fi:
            rdlen, rdsum = fi.read().split()
            return rdlen, rdsum
    except IOError:
            return 0, 0

def calc_readme_checksum():

    readme = open(README_path).read()
    readme_length = len(readme)
    readme_sum    = hashlib.sha256(utf8_to_bytes(readme)).hexdigest()

    return readme_length, readme_sum
    
# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def update_long_descr():
    LONG_DESCR_path = os.path.join(os.path.dirname(__file__), 'LONG_DESCR')
    crdck = calc_readme_checksum()
    rrdck = read_readme_checksum()
    if ((not os.path.exists(LONG_DESCR_path)) or rrdck[1] != crdck[1]):
        if rrdck[1] != crdck[1]:
            print("readme check sum {} does not match readme {}, recalculate LONG_DESCR".format(rrdck[1], crdck[1]))
        try :
            subprocess.check_call(["pandoc", "-f", "markdown", '-t', 'rst', '--ascii', '-o', LONG_DESCR_path, README_path], shell=False)

            # pandoc version before 2.4 seems to write non ascii files even if the ascii flag is given
            # fix this to ensure LONG_DESCR is ASCII, use io.open to make this work with python 2.7
            with io.open(LONG_DESCR_path, "r", encoding="UTF-8") as fi:
                # this creates a byte stream
                inp = fi.read()
            # replace utf8 characters that are generated by pandoc to ASCII
            # and create a byte string 
            ascii_long_desc = inp.replace(u"’","'").replace(u"–","--").replace(u'“','"').replace(u'”','"')

            with open(LONG_DESCR_path, "w") as fw:
                fw.write(ascii_long_desc)
        except (OSError, subprocess.CalledProcessError) as ex:
            print("setup.py::error:: pandoc command failed. Cannot update LONG_DESCR.txt from modified README.md" + str(
                ex))

        write_readme_checksum(crdck[0], crdck[1])
    return open(LONG_DESCR_path).read()


def read_long_descr():
    LONG_DESCR_path = os.path.join(os.path.dirname(__file__), 'LONG_DESCR')
    return open(LONG_DESCR_path).read()

class sdist_subclass(sdist) :
    def run(self):
        # Make sure the compiled Cython files in the distribution are up-to-date
        update_long_descr()
        sdist.run(self)


setup( name = "py_find_1st",
       version = version,
       packages = ['utils_find_1st'],
       ext_package = 'utils_find_1st',
       ext_modules = ext_modules,
       author = "A. Roebel",
       install_requires= install_requires,
       description = "Numpy extension module for efficient search of first array index that compares true",
       cmdclass = {'build_ext': build_ext_subclass, "sdist": sdist_subclass },
       author_email = "axel.dot.roebel@ircam.dot.fr",
        long_description = read_long_descr(),
        license = "GPL",
        url = "http://github.com/roebel/py_find_1st",
        download_url = "https://github.com/roebel/py_find_1st/archive/v{0}.tar.gz".format(version),
        keywords = "numpy,extension,find",
        classifiers = [
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Programming Language :: Python :: 3",
            "Development Status :: 5 - Production/Stable",
            "License :: OSI Approved :: GNU General Public License (GPL)",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: POSIX :: Linux",
            "Operating System :: Microsoft :: Windows",
        ],
       
       # don't install as zip file because those cannot be analyzed by pyinstaller
       zip_safe = False,
    )
