#!/usr/bin/env python3

from ii_functions import *
from getcfg import *
import paths

tossStorage = {}

def outbox_storage_init(outbox_id):
	global tossStorage
	path = os.path.join(paths.tossesdir, outbox_id)
	outbox = outboxFromPath(path)

	outbox, lasttoss = newTossName(outbox)
	tossStorage[outbox_id] = {}
	tossStorage[outbox_id]["storage"] = outbox
	tossStorage[outbox_id]["lasttoss"] = lasttoss

for server in config["servers"]:
	outbox_id = server["outbox_storage_id"]
	outbox_storage_init(outbox_id)

def openEditor(file):
	if (config["defaultEditor"]==True):
		editor=paths.defaultEditorPath
	else:
		editor=config["editor"]

	p=subprocess.Popen(editor+" \""+file+"\"", shell=True)

def edit(message, outbox_id):
	global tossStorage

	if outbox_id == None:
		global config # если пусто, отправляем на первую станцию
		outbox_id = config["servers"][0]["outbox_storage_id"]

	if not outbox_id in tossStorage.keys():
		outbox_storage_init(outbox_id)

	lasttoss = tossStorage[outbox_id]["lasttoss"]
	fname=os.path.join(paths.tossesdir, outbox_id, str(lasttoss)+".toss")
	touch(fname)
	open(fname, "wb").write(message.encode("utf8"))
	openEditor(fname)
	tossStorage[outbox_id]["lasttoss"] += 1

def frmSubj(str):
	if str.startswith("Re: "):
		return str
	else:
		return "Re: "+str

def answer(msgid, outbox_id):
	msg=getMsg(msgid)
	echo=msg.get("echo")
	subj=msg.get("subj")
	to=msg.get("sender")

	template=echo+"\n"+to+"\n"+frmSubj(subj)+"\n\n@repto:"+msgid+"\n"
	edit(template, outbox_id)

def writeNew(echo, outbox_id):
	template=echo+"\nAll\n...\n\n"
	edit(template, outbox_id)