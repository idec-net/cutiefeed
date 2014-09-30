#!/usr/bin/python2
# -*- coding:utf8 -*-

from ii_functions import *

def sendMessages():
	files=os.listdir("out")
	files=[x[:-5] for x in files if x.endswith(".toss")]
	files.sort()
	
	countsent=0
	for file in files:
		f=open("out/"+file+".toss").read()
		
		selectedServer=servers[0]

		for server in servers:
			if(f[0] in server["echoareas"]):
				selectedServer=server
				break

		adress=selectedServer["adress"]
		authstr=selectedServer["authstr"]

		code=base64.b64encode(f)
		
		data = urllib.urlencode({'tmsg': code,'pauth': authstr})
		out = urllib.urlopen(adress + 'u/point', data).read()
		print out
		
		if out.startswith('msg ok'):
			countsent+=1
			os.rename("out/"+file+".toss", "out/"+file+".out")
	return countsent
