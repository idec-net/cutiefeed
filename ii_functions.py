#!/usr/bin/env python2
# -*- coding:utf8 -*-
import os, base64, urllib, subprocess, datetime, hashlib
import paths

def applyBlackList(str):
	return str

def getMsg(msgid):
	try:
		msg=open(paths.msgdir+msgid).read().decode('utf-8').splitlines()
		tags=parseTags(msg[0])
		if('repto' in tags):
			rpt=tags['repto']
		else:
			rpt=False

		message="\n".join(msg[8:])

		meta=dict(repto=rpt,echo=msg[1],time=msg[2],sender=msg[3],addr=msg[4],to=msg[5],subj=msg[6],msg=message,id=msgid)
	except:
		meta=dict(repto=False,echo="",time=0,sender="",addr="",to="",subj="",msg="no message",id=msgid)
	return meta

def b64d(str):
	return base64.b64decode(str)

def hsh(str):
	return base64.urlsafe_b64encode( hashlib.sha256(str).digest() ).replace('-','A').replace('_','z')[:20]

def getfile(file, quiet=False):
	if (not quiet):
		print "fetch "+file
	return urllib.urlopen(file).read()

def touch(fname):
	if os.path.exists(fname):
		os.utime(fname, None)
	else:
		open(fname, 'a').close()

def savemsg(hash, echo, message):
	touch(paths.msgdir+hash)
	touch(paths.indexdir+echo)
	open(paths.msgdir+hash, "w").write(message)
	open(paths.indexdir+echo, "a").write(hash+"\n")

def getMsgList(echo):
	if(os.path.exists(paths.indexdir+echo)):
		return open(paths.indexdir+echo).read().decode('utf-8').splitlines()
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
