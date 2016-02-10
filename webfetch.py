#!/usr/bin/env python3

from ii_functions import *
import network
import os, paths

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

def fetch_messages(adress, firstEchoesToFetch, xcenable=False, one_request_limit=20, fetch_limit=False, from_msgid=False, proxy=None, pervasive_ue=False, callback=None):
	if(len(firstEchoesToFetch)==0):
		return []
	if(xcenable):
		xcfile=os.path.join(paths.datadir, "base-"+hsh(adress))
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
		bottomOffset=fetch_limit
		echoBundle=network.getfile(adress+"u/e/"+"/".join(echoesToFetch)+"/-"+str(bottomOffset)+":"+str(fetch_limit), proxy)
	else:
		echoBundle=network.getfile(adress+"u/e/"+"/".join(echoesToFetch), proxy)

	localIndex={}

	for echo in echoesToFetch:
		print("loading local echo "+echo)
		localIndex[echo]=getMsgList(echo)

	remoteEchos2d=parseFullEchoList(echoBundle)
	
	commondiff={} # это все новые сообщения, которые надо будет скачать

	nextfetch=[]
	for echo in echoesToFetch:
		localMessages=localIndex[echo]
		remoteMessages=remoteEchos2d[echo]
		commondiff[echo]=[i for i in remoteMessages if i not in localMessages]

		if pervasive_ue==True and len(remoteMessages) == len(commondiff[echo]):
			nextfetch.append(echo)
	
	# и вот начинается магия
	while (len(nextfetch) > 0):
		bottomOffset+=fetch_limit
		echoBundle=network.getfile(adress+"u/e/"+"/".join(nextfetch)+"/-"+str(bottomOffset)+":"+str(fetch_limit), proxy)
		msgsDict=parseFullEchoList(echoBundle)

		for echo in nextfetch:
			localMessages=localIndex[echo]
			remoteMessages=msgsDict.get(echo)
	
			if remoteMessages == None:
				nextfetch.remove(echo)
				continue
			
			# добавляем нужные элементы в начало
			diff=[i for i in remoteMessages if i not in localMessages and i not in commondiff[echo]]
			commondiff[echo]=diff + commondiff[echo]
			# если мы всё, то удаляем эху из списка получения
			if len(remoteMessages) != len(diff):
				nextfetch.remove(echo)

	print("making assoc dict: msgid -> echo")

	echodict={}
	for echo, echolist in commondiff.items():
		for msgid in echolist:
			echodict[msgid]=echo

	difference=[] # делаем так, чтобы расставить сообщения в нужном порядке
	for echo in commondiff.keys():
		difference+=[msgid for msgid in commondiff[echo]]
	
	print("apply blacklist to remote echoareas")

	difference=blacklist_func.applyBlacklist(difference)
	difference2d=[difference[i:i+one_request_limit] for i in range(0, len(difference), one_request_limit)]

	savedMessages=[]
	
	for diff in difference2d:
		impldifference="/".join(diff)
		fullbundle=network.getfile(adress+"u/m/"+impldifference, proxy)

		bundles=fullbundle.splitlines()
		for bundle in bundles:
			arr=bundle.split(":")
			bundleMsgids=[]
			if(arr[0]!="" and arr[1]!=""):
				msgid=arr[0]; message=b64d(arr[1])
				echo=echodict[msgid]
				print("savemsg "+msgid+" to "+echo)
				savedMessages.append(msgid)
				bundleMsgids.append(msgid)
				savemsg(msgid, echo, message)
			if callback != None:
				callback(bundleMsgids)
				
	return savedMessages
