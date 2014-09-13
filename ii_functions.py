#!/usr/bin/env python2
# -*- coding:utf8 -*-
import os, base64, json, urllib, subprocess, datetime, hashlib

configFile=open("config.json")
config=json.load(configFile)
adress=config["adress"]
echoareas=config["echoareas"]
authstr=config["authstr"]
editor=config["editor"]
xtenable=config["xtenable"]

def applyBlackList(str):
	return str

def getMsg(msgid):
	try:
		msg=open("msg/"+msgid).read().decode('utf-8').splitlines()
		tags=parseTags(msg[0])
		if('repto' in tags):
			rpt=tags['repto']
		else:
			rpt=False

		message="\n".join(msg[8:])

		meta=dict(repto=rpt,echo=msg[1],time=msg[2],sender=msg[3],addr=msg[4],to=msg[5],subj=msg[6],msg=message,id=msgid)
	except:
		meta=dict(repto=False,echo="",time=0,sender="",addr="",to="",subj="",msg="no message")
	return meta

def b64d(str):
	return base64.b64decode(str)

def hsh(str):
	return base64.urlsafe_b64encode( hashlib.sha256(str).digest() ).replace('-','A').replace('_','z')[:20]

def getfile(file):
	print "fetch "+file
	return urllib.urlopen(file).read()

def touch(fname):
	if os.path.exists(fname):
		os.utime(fname, None)
	else:
		open(fname, 'a').close()

def savemsg(hash, echo, message):
	touch("msg/"+hash)
	touch("echo/"+echo)
	open("msg/"+hash, "w").write(message)
	open("echo/"+echo, "a").write(hash+"\n")

def getLocalEcho(echo):
	if(not os.path.exists("echo/"+echo)):
		return ""
	else:
		return open("echo/"+echo).read()

def getMsgList(echo):
	if(os.path.exists("echo/"+echo)):
		return open("echo/"+echo).read().decode('utf-8').splitlines()
	else:
		return []

def formatDate(time):
	return datetime.datetime.fromtimestamp(int(time)).strftime("%Y-%m-%d (%A), %H:%M").decode("utf8")

def parseTags(str):
	arr=str.split("/")
	tags={}
	for i in range(0,len(arr),2):
		if(arr[i+1]):
			tags[arr[i]]=arr[i+1]
		
	return tags
