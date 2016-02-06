#!/usr/bin/env python3

from ii_functions import *
from getcfg import *
import network
import urllib.parse
import paths

def sendMessages(proxy=None):
	files=os.listdir(paths.tossesdir)
	files=[x[:-5] for x in files if x.endswith(".toss")]
	files.sort()
	
	countsent=0
	for file in files:
		f=read_file(os.path.join(paths.tossesdir, file+".toss"))
		
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

		out = network.getfile(adress + 'u/point', proxy, data)
		print(out)
		
		if out.startswith('msg ok'):
			countsent+=1
			one=os.path.join(paths.tossesdir, file+".toss")
			two=os.path.join(paths.tossesdir, file+".out")

			os.rename(one, two)
	return countsent
