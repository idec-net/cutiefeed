#!/usr/bin/env python3

import json, os, paths

if (not os.path.exists(paths.configfile) and os.path.exists(paths.configfile_default)):
	import shutil
	print("Warning: could not find config. Trying to copy default one to it.")
	shutil.copyfile(paths.configfile_default, paths.configfile)

try:
	configFile=open(paths.configfile)
	config=json.load(configFile)
	configFile.close()

except Exception as e:
	print("Caught exception: "+str(e))
	print("Error: can't load config. Exiting.")
	print("Может быть, у тебя конфиг в INI, а не в json? Удали-ка его лучше: ("+paths.configfile+")")
	exit()

servers=config["servers"]

defaultValues={
	"servers": [dict()],
	"offline-echoareas": [],
	"editor": "",
	"proxy": "http://user:pass@localhost:8080",
	"proxyType": "http",
	"defaultEditor": False,
	"firstrun": True,
	"autoSaveChanges": True,
	"useProxy": False
}

defaultServersValues={
	"adress": "http://ii-net.tk/ii/ii-point.php?q=/",
	"authstr": "",
	"echoareas": ["ii.test.14", "mlp.15"],
	"xcenable": True,
	"advancedue": False,
	"uelimit": 200
}

for key in defaultValues.keys():
	if not key in config.keys():
		config[key]=defaultValues[key]

i=0
for server in config["servers"]:
	for key in defaultServersValues:
		if not key in server:
			config["servers"][i][key]=defaultServersValues[key]
	i+=1

print("Config loaded")

def saveConfig():
	try:
		configFile=open(paths.configfile, "w")
		json.dump(config, configFile)
		configFile.close()
	except Exception as e:
		print("Caught exception while saving: "+str(e))
		return False
	return True

for directory in [paths.datadir, paths.indexdir, paths.msgdir, paths.tossesdir]:
	if not os.path.exists(directory):
		print("Directory "+directory+" does not exist. Creating...")
		os.makedirs(directory)
