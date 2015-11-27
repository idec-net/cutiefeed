#!/usr/bin/env python3

from ii_functions import *
from getcfg import *
import paths

tosses=[int(i.strip(".toss").strip(".out")) for i in os.listdir(paths.tossesdir)]
tosses.sort()

if(len(tosses)==0):
	tosses.append(0)
lasttoss=tosses[len(tosses)-1]+1

def openEditor(file):
	if (config["defaultEditor"]==True):
		editor=paths.defaultEditorPath
	else:
		editor=config["editor"]
	
	p=subprocess.Popen(editor+" "+file, shell=True)

def edit(message):
	global lasttoss
	fname=paths.tossesdir+str(lasttoss)+".toss"
	touch(fname)
	open(fname, "w").write(message)
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
