#!/usr/bin/env python3

import os, base64, subprocess, datetime, hashlib, cgi
import paths
import blacklist_func

def read_file(filename):
	with open(filename, "rb") as p:
		return p.read().decode("utf8")

def getMsg(msgid):
	try:
		msg=read_file(paths.msgdir+msgid).splitlines()
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

def getMsgEscape(msgid): # получаем сообщение и режем html в нужных частях
	m=getMsg(msgid)
	values=["sender", "subj", "addr", "to", "msg", "repto"]
	for value in values:
		if (type(m[value]) == bool): # если repto == False (для совместимости), ибо нельзя обрабатывать не строку
			continue

		m[value]=cgi.escape(m[value], True)
	
	return m

def getOutMsg(name):
	try:
		source=read_file(paths.tossesdir+name).splitlines()
		
		str=source[4]
		if str.startswith("@repto:"):
			repto=str[7:]
			msgtext="\n".join(source[5:])
		else:
			repto=False
			msgtext="\n".join(source[4:])
		
		meta=dict(echo=source[0], to=source[1], subj=source[2], repto=repto, msg=msgtext)
	except:
		meta=dict(echo="", to="All", subj="", repto=False, msg="")
	return meta

def getOutMsgEscape(name): # получаем сообщение и режем html в нужных частях
	m=getOutMsg(name)
	values=["echo", "to", "subj", "repto", "msg"]
	for value in values:
		if (type(m[value]) == bool): # для repto
			continue

		m[value]=cgi.escape(m[value], True)
	
	return m

def getOutList():
	files=os.listdir(paths.tossesdir)
	files=[x for x in files if x.endswith(".toss") or x.endswith(".out")]
	files.sort(key=lambda x: int(x.strip(".toss").strip(".out")))
	return files

def b64d(str):
	return base64.b64decode(str)

def hsh(str):
	return base64.urlsafe_b64encode( hashlib.sha256(bytes(str, "utf8")).digest() ).decode("utf8").replace('-','A').replace('_','z')[:20]

def touch(fname):
	if os.path.exists(fname):
		os.utime(fname, None)
	else:
		open(fname, 'a').close()

def savemsg(hash, echo, message):
	touch(paths.msgdir+hash)
	touch(paths.indexdir+echo)
	open(paths.msgdir+hash, "wb").write(message)
	open(paths.indexdir+echo, "a").write(hash+"\n")

def getMsgList(echo):
	if(os.path.exists(paths.indexdir+echo)):
		arr=read_file(paths.indexdir+echo).splitlines()
		return blacklist_func.applyBlacklist(arr)
	else:
		return []

def formatDate(time):
	return datetime.datetime.fromtimestamp(int(time)).strftime("%Y-%m-%d (%A), %H:%M")

def parseTags(str):
	arr=str.split("/")
	tags={}
	for i in range(0,len(arr),2):
		if(arr[i+1]):
			tags[arr[i]]=arr[i+1]
		
	return tags
