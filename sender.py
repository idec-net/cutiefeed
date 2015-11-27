#!/usr/bin/env python3

from ii_functions import *
from getcfg import *
import paths

def sendMessages():
	files=os.listdir(paths.tossesdir)
	files=[x[:-5] for x in files if x.endswith(".toss")]
	files.sort()
	
	countsent=0
	for file in files:
		f=open(paths.tossesdir+file+".toss").read()
		
		adress=servers[0]["adress"]
		authstr=servers[0]["authstr"]

		for server in servers:
			if(f.splitlines()[0] in server["echoareas"]):
				adress=server["adress"]
				authstr=server["authstr"]
				break
		
		code=base64.b64encode(bytes(f, "utf8"))
		
		data = urllib.parse.urlencode({'tmsg': code,'pauth': authstr}).encode("utf8")
		print(adress)
		print(authstr)
		out = urllib.request.urlopen(adress + 'u/point', data).read()
		print(out)
		
		if out.startswith(b'msg ok'):
			countsent+=1
			os.rename(paths.tossesdir+file+".toss", paths.tossesdir+file+".out")
	return countsent
