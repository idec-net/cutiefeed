#!/usr/bin/env python2
# -*- coding:utf8 -*-
import json, os, paths

if (not os.path.exists(paths.configfile) and os.path.exists(paths.configfile_default)):
	import shutil
	print "Warning: could not find config. Trying to copy default one to it."
	shutil.copyfile(paths.configfile_default, paths.configfile)

try:
	configFile=open(paths.configfile)
	config=json.load(configFile)
	configFile.close()

except Exception, e:
	print "Caught exception: "+str(e)
	print "Error: can't load config. Exiting."
	exit()

servers=config["servers"]
print "Config loaded"

def saveConfig():
	try:
		configFile=open(paths.configfile, "w")
		json.dump(config, configFile)
		configFile.close()
	except Exception, e:
		print "Caught exception while saving: "+str(e)
		return False
	return True

for directory in [paths.datadir, paths.indexdir, paths.msgdir, paths.tossesdir]:
	if not os.path.exists(directory):
		print "Directory "+directory+" does not exist. Creating..."
		os.makedirs(directory)
