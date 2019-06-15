#!/usr/bin/env python3

import os

homedir="data/"
cwd=os.getcwd()
configfile=os.path.join(homedir, ".iicli-modular")

datadir=os.path.join(homedir, ".local/share/iicli-modular/")
indexdir=os.path.join(datadir, "echo/")
msgdir=os.path.join(datadir, "msg/")
tossesdir=os.path.join(datadir, "out/")
subjcachedir=os.path.join(datadir, "subjcache/")
echopositionfile=os.path.join(datadir, "positioncache.json")
blacklistfile=os.path.join(datadir, "blacklist.txt")

configfile_default=os.path.join(cwd, "config.default.json")
defaultEditorPath="tossedit.exe"
