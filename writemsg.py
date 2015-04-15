#!/usr/bin/env python2
# -*- config:utf8 -*-
from ii_functions import *
from getcfg import *

tosses=[int(i.strip(".toss").strip(".out")) for i in os.listdir("out")]
tosses.sort()

if(len(tosses)==0):
	tosses.append(0)
lasttoss=tosses[len(tosses)-1]+1

def openEditor(file):
	p=subprocess.Popen(config["editor"]+" "+file, shell=True)

def edit(message):
	global lasttoss
	fname="out/"+str(lasttoss)+".toss"
	touch(fname)
	open(fname, "w").write(message.encode("utf8"))
	openEditor(fname)
	lasttoss+=1

def writeNew(echo):
	template=echo+"\nAll\n...\n\n"
	edit(template)

def frmSubj(str):
	if str.startswith("Re: "):
		return str
	else:
		return "Re: "+str

def answer(echo, msgid):
	msg=getMsg(msgid)
	subj=msg.get("subj")
	to=msg.get("sender")

	template=echo+"\n"+to+"\n"+frmSubj(subj)+"\n\n@repto:"+msgid+"\n"
	edit(template)
