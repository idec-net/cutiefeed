#!/usr/bin/env python3

from tkinter import *
from tkinter.ttk import *
import tkinter.messagebox

import locale
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

from getcfg import *
from ii_functions import *
import webfetch
import writemsg
import sender

def exc(cmd):
	exec(compile(cmd, "<string>", "exec"))

def myfunction(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

def updatemsg():
	global msgnumber,msgid_answer
	lb.selection_clear(0, len(msglist)-1)
	lb.select_set(msgnumber)
	msg=getMsg(msglist[msgnumber])
	msgid_answer=msg.get('id')
	msgtext="msgid: "+msgid_answer+"\n"+formatDate(msg.get('time'))+"\n"+msg.get('subj')+"\n"+msg.get('sender')+" -> "+msg.get('to')+"\n\n"+msg.get('msg')
	txt.delete("1.0",END)
	txt.insert(INSERT,msgtext)
	txt.tag_add("sender", "4.0", "4.end")
	txt.tag_config("sender",font=('Monospace',10,'bold'))

def msgminus(event):
	global msgnumber
	if(msgnumber>0):
		msgnumber-=1;
		updatemsg()

def msgplus(event):
	global msgnumber
	if(msgnumber<=listlen):
		msgnumber+=1;
		updatemsg()

def lbselect(event):
	global msgnumber
	msgnumber=lb.curselection()[0]
	updatemsg()

def c_writeNew(event):
	writemsg.writeNew(echoarea)

def displayEchoList(event):
	root.destroy()
	mainwindow()

def getNewMessages(event):
	root.destroy()
	getDialog()

def sendWrote(event):
	countsent=sender.sendMessages()
	tkinter.messagebox.showinfo("", "Отправлено сообщений: "+str(countsent))

def answer(event):
	writemsg.answer(echoarea, msgid_answer)

def mainwindow():
	global buttonsframe,root,canvas
	root=Tk()
	Style().theme_use("clam")
	
	root.title("Список эх")
	root.minsize(200,100)
	
	frame1=Frame(root, relief=GROOVE)
	canvas=Canvas(frame1)
	buttonsframe=Frame(canvas)

	getbutton=Button(buttonsframe,text="Получить сообщения")
	getbutton.pack(side='top')
	getbutton.bind("<Button-1>",getNewMessages)

	def addButtons(echoareas):
		for i in range(0,len(echoareas)):
			exc("global but"+str(i)+"""
but"""+str(i)+"=Button(buttonsframe,text='"+echoareas[i]+"')"+"""
def callb"""+str(i)+"(event):"+"""
	global root"""+"""
	root.destroy()"""+"""
	viewwindow('"""+echoareas[i]+"""')
but"""+str(i)+".bind('<Button-1>',callb"+str(i)+""")
but"""+str(i)+".pack()")

	for server in servers:
		echoareas=server["echoareas"]
		Label(buttonsframe,text=server["adress"]).pack()
		addButtons(server["echoareas"])
	
	if(len(config["offline-echoareas"])>0):
		Label(buttonsframe,text="Эхи без сервера").pack()
		addButtons(config["offline-echoareas"])

	buttonsframe.pack(fill='both', expand=True)
	scroll=Scrollbar(frame1, command=canvas.yview)
	canvas.configure(yscrollcommand=scroll.set)
	canvas.pack(side='left', fill='both', expand=True)

	buttonsframe.pack(fill='both', expand=True)
	frame1.pack(fill='both', expand=True)
	scroll.pack(side='right', fill='y')
	canvas.create_window((1,1),window=buttonsframe,anchor='nw')
	buttonsframe.bind("<Configure>",myfunction)
	
	root.mainloop()

def viewwindow(echo):
	global root,lb,msglist,txt,msgnumber,listlen,echoarea
	root=Tk()
	Style().theme_use("clam")
	echoarea=echo

	root.title(echo)
	root.minsize(200,100)
	
	msglist=getMsgList(echo)
	msglist.reverse()

	msgnumber=0
	listlen=len(msglist)-2

	lbframe=Frame(root)
	topframe=Frame(root)
	txtframe=Frame(root)

	lbframe.pack(side='left', fill='both', expand=True)
	topframe.pack(side='top')
	txtframe.pack(side='right', fill='both', expand=True)
	
	button1=Button(topframe,text="<")
	button2=Button(topframe,text=">")
	back=Button(topframe,text="К списку эх")
	loadbut=Button(topframe,text="Скачать сообщения")
	newbut=Button(topframe,text="Новое")
	answframe=Button(topframe,text="Ответить")
	sendframe=Button(topframe,text="Отправить сообщения")

	button1.bind("<Button-1>",msgminus)
	button2.bind("<Button-1>",msgplus)
	back.bind("<Button-1>",displayEchoList)
	newbut.bind("<Button-1>",c_writeNew)
	loadbut.bind("<Button-1>",getNewMessages)
	sendframe.bind("<Button-1>",sendWrote)
	answframe.bind("<Button-1>",answer)

	back.pack(side='left')
	button1.pack(side='left')
	button2.pack(side='left')
	
	loadbut.pack(side='right')
	newbut.pack(side='right')
	answframe.pack(side='right')
	sendframe.pack(side='right')

	lb=Listbox(lbframe,selectmode=SINGLE)
	
	for i in range(listlen+2):
		lb.insert(END, getMsg(msglist[i]).get('subj'))
	lb.bind("<<ListboxSelect>>",lbselect)
	lb.pack(side='left', fill='both', expand=True)
	
	txt=Text(txtframe,wrap=WORD)
	updatemsg()
	
	scroll1=Scrollbar(txtframe)
	scroll1.pack(side=RIGHT, fill=Y)
	
	scroll2=Scrollbar(lbframe)
	scroll2.pack(side=RIGHT, fill=Y)
	
	txt.config(yscrollcommand=scroll1.set)
	scroll1.config(command=txt.yview)
	
	lb.config(yscrollcommand=scroll2.set)
	scroll2.config(command=lb.yview)

	txt.pack(side='right', fill='both', expand=True)
	
	root.mainloop()

def getDialog():
	global root
	root=Tk()
	Style().theme_use("clam")
	root.title("Получение сообщений")
	root.minsize(200,100)

	butframe=Frame(root)
	txtframe=Frame(root)

	text=Text(txtframe, wrap=WORD)
	text.pack(side='left', fill='both', expand=True)
	
	echosback=Button(butframe, text='К списку эх')
	echosback.bind("<Button-1>",displayEchoList)

	scroll=Scrollbar(txtframe)
	scroll.pack(side='right', fill=Y)

	text.config(yscrollcommand=scroll.set)
	scroll.config(command=text.yview)

	butframe.pack(side='top')
	echosback.pack(side='right')
	txtframe.pack(fill='both',expand=True)

	msgids=[]
	for server in servers:
		msgidsNew=webfetch.fetch_messages(server["adress"], server["echoareas"], server["xcenable"])
		msgids+=msgidsNew

	if len(msgids)==0:
		text.insert(INSERT, 'Новых сообщений нет.')
	else:
		text.insert(INSERT, 'Новые сообщения:')
		for msgid in msgids:
			arr=getMsg(msgid)
			txt="\n\n"+arr.get('echo')+"\nmsgid: "+arr.get('id')+"\n"+formatDate(arr.get('time'))+"\n"+arr.get('subj')+"\n"+arr.get('sender')+" -> "+arr.get('to')+"\n\n"+arr.get('msg')
			text.insert(INSERT, txt)

	root.mainloop()

mainwindow()
