#!/usr/bin/env python3

from socks import monkey_patch as socks_proxy_monkey_patch
socks_proxy_monkey_patch.monkey_patch()

import urllib.request

from socks import socks_proxy_context

def getfile(file, proxy=None, data=None, return_descriptor=False, quiet=False):
	if (not quiet):
		print("fetch "+file)
	
	p = None
	
	if proxy == None:
		if (urllib.request._opener != None):
			urllib.request.install_opener(None)
	elif (proxy != None and "http" in proxy.keys()):
		handler=urllib.request.ProxyHandler(proxy)
		opener=urllib.request.build_opener(handler)
		urllib.request.install_opener(opener)
	elif ("socks" in proxy.keys()):
		keys=proxy["socks"].split(":")
		url=keys[0]
		port=int(keys[1])
		
		with socks_proxy_context.socks_proxy_context(proxy_address=(url, port)):
			p = urllib.request.urlopen(file, data, timeout=20.0)
	
	if not p:
		p = urllib.request.urlopen(file, data)
	
	if return_descriptor:
		return p
	else:
		return p.read().decode("utf8")
