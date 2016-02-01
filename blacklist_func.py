import os, paths

def delete(filename, verbose=True):
	if(not os.path.exists(filename)):
		if (verbose):
			print("Файл "+filename+" не существует!")
		return
	try:
		print("rm "+filename)
		os.remove(filename)
	except:
		if(verbose):
			print("Ошибка удаления, проверьте права")

def getBlackList(filename=paths.blacklistfile):
	if not os.path.exists(filename):
		open(filename, "a").close()
	
	arr=open(filename).read().splitlines()
	arr=[x for x in arr if x != ""]
	return arr

def blacklistCleanup(echoes):
	global blacklist
	for echo in echoes:
		if(os.path.exists(paths.indexdir+echo)):
			msglist=open(paths.indexdir+echo).read().splitlines()
		else:
			continue
		
		msglist=[x for x in msglist if x not in blacklist]
		print("saving echo "+echo)
		f=open(os.path.join(paths.indexdir, echo), "w")
		f.write("\n".join(msglist)+"\n")
		f.close()
	print("cleaning messages")
	for msgid in blacklist:
		delete(os.path.join(paths.msgdir, msgid))

def applyBlacklist(echo):
	global blacklist
	echo=[x for x in echo if x not in blacklist]
	return echo

blacklist=getBlackList()
