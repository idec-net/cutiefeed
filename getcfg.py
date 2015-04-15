#!/usr/bin/env python2
# -*- coding:utf8 -*-
import ConfigParser,os

iniparser=ConfigParser.ConfigParser()
if (not os.path.exists("config.ini") and os.path.exists("config.default.ini")):
	import shutil
	print "Warning: could not find config. Trying to copy default one to it."
	shutil.copyfile("config.default.ini", "config.ini")

if (not iniparser.read("config.ini")):
	print "Error: can't load config. Exiting."
	exit()

config={}
config["servers"]=[]
config["offline-echoareas"]=[]
config["editor"]="nano"

sections=iniparser.sections()
for section in sections:
	if (section != "Additions"):
		newserver={}
		for option in ["adress", "authstr", "xtenable"]:
			try:
				newserver[option]=iniparser.get(section, option)
				if(option=="xtenable" and newserver[option]=="true"): newserver[option]=True;
			except:
				print "Error: can't read option "+option+" from section "+section+". Exiting."
				exit()

		newserver["echoareas"]=iniparser.get(section, "echoareas").strip().splitlines()
		config["servers"].append(newserver)
	else:
		config["editor"]=iniparser.get(section, "editor")
		config["offline-echoareas"]=iniparser.get(section, "offline-echoareas").strip().splitlines()

servers=config["servers"]
print "Config loaded"
