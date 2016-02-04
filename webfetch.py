#!/usr/bin/env python3

from ii_functions import *
import network
import paths

def parseFullEchoList(echobundle):
	echos2d={}
	echobundle=echobundle.splitlines()
	lastecho=""

	for element in echobundle:
		if element:
			if "." not in element:
				echos2d[lastecho].append(element)
			else:
				lastecho=element
				echos2d[lastecho]=[]
	return echos2d

def fetch_messages(adress, firstEchoesToFetch, xcenable=False, one_request_limit=20, fetch_limit=False, from_msgid=False, proxy=None, callback=None):
	if(len(firstEchoesToFetch)==0):
		return []
	if(xcenable):
		xcfile=paths.datadir+"base-"+hsh(adress)
		donot=[]
		try:
			f=read_file(xcfile).splitlines()
		except:
			touch(xcfile)
			open(xcfile, "w").write("\n".join([x+":0" for x in firstEchoesToFetch]))
			f=False
		if(f):
			remotexcget=network.getfile(adress+"x/c/"+"/".join(firstEchoesToFetch), proxy)
			remotexc=[x.split(":") for x in remotexcget.splitlines()]
			
			if(len(f)==len(remotexc)):
				xcdict={}
				for x in remotexc:
					xcdict[x[0]]=int(x[1])
				localdict={}
				for x in [i.split(":") for i in f]:
					localdict[x[0]]=int(x[1])
			
				for echo in firstEchoesToFetch:
					if int(xcdict[echo])==int(localdict[echo]):
						donot.append(echo)
						print("removed "+echo)
				
			open(xcfile, "w").write(remotexcget)
			
		echoesToFetch=[x for x in firstEchoesToFetch if x not in donot]
	else:
		echoesToFetch=firstEchoesToFetch

	if(len(echoesToFetch)==0):
		return []
	
	if (fetch_limit != False):
		echoBundle=network.getfile(adress+"u/e/"+"/".join(echoesToFetch)+"/-"+str(fetch_limit)+":"+str(fetch_limit), proxy)
	else:
		echoBundle=network.getfile(adress+"u/e/"+"/".join(echoesToFetch), proxy)
	
	remoteEchos2d=parseFullEchoList(echoBundle)
	savedMessages=[]
	
	for echo in echoesToFetch:
		localMessages=getMsgList(echo)
		
		remoteMessages=remoteEchos2d[echo]

		difference=[i for i in remoteMessages if i not in localMessages]
		difference=blacklist_func.applyBlacklist(difference)

		difference2d=[difference[i:i+one_request_limit] for i in range(0, len(difference), one_request_limit)]
		
		for diff in difference2d:
			print(echo)
			impldifference="/".join(diff)
			fullbundle=network.getfile(adress+"u/m/"+impldifference, proxy)
	
			bundles=fullbundle.splitlines()
			for bundle in bundles:
				arr=bundle.split(":")
				bundleMsgids=[]
				if(arr[0]!="" and arr[1]!=""):
					msgid=arr[0]; message=b64d(arr[1])
					print("savemsg "+msgid)
					savedMessages.append(msgid)
					bundleMsgids.append(msgid)
					savemsg(msgid, echo, message)
				if callback != None:
					callback(bundleMsgids)
					
	return savedMessages
