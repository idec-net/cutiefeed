#!/usr/bin/env python2
# -*- coding: utf8 -*-

import os

homedir=os.path.expanduser("~")
cwd=os.getcwd()
configfile=os.path.join(homedir, ".iicli-modular")

datadir=os.path.join(homedir, ".local/share/iicli-modular/")
indexdir=os.path.join(datadir, "echo/")
msgdir=os.path.join(datadir, "msg/")
tossesdir=os.path.join(datadir, "out/")

configfile_default=os.path.join(cwd, "config.default.ini")
