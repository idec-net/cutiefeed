#!/usr/bin/env python3

from ii_functions import *
from getcfg import *
import network
import urllib.parse
import paths

def sendMessages(proxy=None, error_callback=None):
	countsent=0
	for server in servers:
		namespace = server["outbox_storage_id"]
		storage_path = os.path.join(paths.tossesdir, namespace)

		files = scanForTosses(storage_path)
		if len(files) == 0:
			continue

		adress=server["adress"]
		authstr=server["authstr"]

		for file in files:
			toss_path = os.path.join(storage_path, file + ".toss")
			f=read_file(toss_path)
			code=base64.b64encode(bytes(f, "utf8"))

			params = {'tmsg': code,'pauth': authstr}
			data = urllib.parse.urlencode(params).encode("utf8")
			print(adress)

			out = network.getfile(adress + 'u/point', proxy, data)
			print(out)

			if out.startswith('msg ok'):
				countsent+=1
				one=os.path.join(storage_path, file+".toss")
				two=os.path.join(storage_path, file+".out")
				os.rename(one, two)
			elif (error_callback != None):
				error_callback(toss_path, out)
	return countsent