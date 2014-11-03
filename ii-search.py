#!/usr/bin/env python2
#-*- coding: utf8 -*-

import os,datetime
from ii_functions import *

def getReadableMsg(msg):
	msgid=msg.get('id')
	subj=msg.get('subj')
	sender=msg.get('sender')
	addr=msg.get('addr')
	to=msg.get('to')

	if(msg['repto']):
		repto=msg.get("repto")
	else:
		repto=u"-"

	msgtext="msgid: "+msgid+"\n"+u"Ответ на: "+repto+"\n"+formatDate(msg.get('time'))+"\n"+subj+"\n"+sender+" ("+addr+")  ->  "+to+"\n\n"+msg.get("msg")
	return msgtext
def sortByTime(msg):
	return float(msg.get("time"))

echo=raw_input("Введите нужную эху(эхи): ").decode("utf8").split(" ")
senders=raw_input("Введите поинтов-отправителей: ").decode("utf8").split(" ")
receivers=raw_input("Введите поинтов-получателей: ").decode("utf8").split(" ")
address=raw_input("Адрес станции поинта (разделитель ||): ").decode("utf8").split("||")
timeprom=raw_input("Введите промежуток времени в формате '20140805 20140920': ").decode("utf8").split(" ")
subj=raw_input("Введите тему сообщения: ").decode("utf8")
text=raw_input("Введите строку для поиска: ").decode("utf8")

dformat="%Y%m%d"
dateone=datetime.datetime(1970,1,1)
datetwo=datetime.datetime.today()
if(len(timeprom)==2):
	dateone=datetime.datetime.strptime(timeprom[0], dformat)
	datetwo=datetime.datetime.strptime(timeprom[1], dformat)

index=[]
if(not echo[0]):
	for echoarea in os.listdir("echo/"):
		index+=getLocalEcho(echoarea).splitlines()
else:
	for x in echo:
		index+=getLocalEcho(x).splitlines()

if(len(index)<=0):
	print "База пуста (проверьте права доступа)."
	exit()

print "Загрузка базы..."
msglist={}
removelist=[]
for x in index:
	msglist[x]=getMsg(x)

print "Фильтрация сообщений...\n"
for msg in msglist.itervalues():
	for point in senders:
		if(str(point) in msg["sender"]):
			c=True
			break
	d=False
	for addr in address:
		if(str(addr) in msg["addr"]):
			d=True
			break
	e=False
	for point in receivers:
		if(str(point) in msg["to"]):
			e=True
			break

	msgdate=datetime.datetime.fromtimestamp(float(msg.get("time")))

	if (
		(c==False) or
		(d==False) or
		(e==False) or
		(subj not in msg["subj"]) or
		(text not in msg["msg"]) or
		(msgdate<dateone) or
		(msgdate>datetwo)
	):
		if(msg.get("id")):
			removelist.append(msg["id"])

for i in removelist:
	msglist.__delitem__(i)

if(len(msglist)==0):
	print "Сообщения не найдены."
else:
	print "Найдено сообщений: "+str(len(msglist))
	for msg in sorted(msglist.itervalues(), key=sortByTime):
		print "====----===="
		print getReadableMsg(msg)
