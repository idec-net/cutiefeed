#!/usr/bin/env python3

from ii_functions import *
from getcfg import *
import paths

def sendMessages(proxy=None):
	if proxy == None:
		if (urllib.request._opener != None):
			urllib.request.install_opener(None)
		context=None
	elif (proxy != None and "http" in proxy.keys()):
		handler=urllib.request.ProxyHandler(proxy)
		opener=urllib.request.build_opener(handler)
		urllib.request.install_opener(opener)
		context=None
	elif (proxy != None and "socks" in proxy.keys()):
		keys=proxy["socks"].split(":")
		url=keys[0]
		port=int(keys[1])
		context=True
	
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

		if context!=None:
			with socks_proxy_context.socks_proxy_context(proxy_address=(url, port)):
				out = urllib.request.urlopen(adress + 'u/point', data).read()
		else:
			out = urllib.request.urlopen(adress + 'u/point', data).read()

		print(out.decode("utf8"))
		
		if out.startswith(b'msg ok'):
			countsent+=1
			os.rename(paths.tossesdir+file+".toss", paths.tossesdir+file+".out")
	return countsent
