#!/usr/bin/env python2
# -*- coding:utf8 -*-
import locale,sys
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

from ii_functions import *
import webfetch
import writemsg
import sender

from PyQt4 import QtCore, QtGui, uic

def updatemsg():
	global msgnumber,msgid_answer,slf,msglist
	msg=getMsg(msglist[msgnumber])
	msgid_answer=msg.get('id')
	msgtext="msgid: "+msgid_answer+"\n"+formatDate(msg.get('time'))+"\n"+msg.get('subj')+"\n"+msg.get('sender')+" -> "+msg.get('to')+"\n\n"+msg.get('msg')

	slf.listWidget.setCurrentRow(msgnumber)
	slf.textEdit.setText(msgtext)

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

def lbselect():
	global msgnumber,slf
	msgnumber=slf.listWidget.currentRow()
	updatemsg()

def c_writeNew(event):
	global echo
	writemsg.writeNew(echo)

def sendWrote(event):
	countsent=sender.sendMessages()
	box=QtGui.QMessageBox()
	box.setText(u"Отправлено сообщений: "+str(countsent))
	box.exec_()

def answer(event):
	global echo,msgid_answer
	writemsg.answer(echo, msgid_answer)

class Form(QtGui.QMainWindow):
	def __init__(self):
		super(Form, self).__init__()
		self.mainwindow()
		global slf,msglist,msgnumber,listlen
		slf=self

	def exc(self,cmd):
		exec compile(cmd, "<string>", "exec")

	def mainwindow(self):
		uic.loadUi("mainwindow.ui",self)

		for i in range(0,len(echoareas)):
			cmd="self.but"""+str(i)+"=QtGui.QPushButton('"+echoareas[i]+"',self)"+"""
def callb"""+str(i)+"(event):"+"""
	slf.viewwindow('"""+echoareas[i]+"""')
self.but"""+str(i)+".clicked.connect(callb"+str(i)+""")
self.verticalLayout_2.addWidget(self.but"""+str(i)+")"
			self.exc(cmd)

	def viewwindow(self, echoarea):
		global msglist,msgnumber,listlen,echo
		echo=echoarea
	
		uic.loadUi("viewwindow.ui",self)
		self.setWindowTitle(u"Просмотр сообщений: "+echoarea)
	
		msglist=getMsgList(echoarea)
		msglist.reverse()

		msgnumber=0
		listlen=len(msglist)-2

		for i in range(listlen+2):
			self.listWidget.addItem(getMsg(msglist[i]).get('subj'))

		self.listWidget.currentRowChanged.connect(lbselect)
		updatemsg()

		self.pushButton.clicked.connect(self.mainwindow)
		self.pushButton_2.clicked.connect(msgminus)
		self.pushButton_3.clicked.connect(msgplus)
		self.pushButton_4.clicked.connect(sendWrote)
		self.pushButton_5.clicked.connect(answer)
		self.pushButton_6.clicked.connect(c_writeNew)
		self.pushButton_7.clicked.connect(self.getDialog)

	def getDialog(self):
		uic.loadUi("getwindow.ui",self)
		self.pushButton.clicked.connect(self.getNewText)
		self.pushButton_2.clicked.connect(self.mainwindow)
		self.getNewText()
	
	def getNewText(self):
		msgids=webfetch.fetch_messages(adress, echoareas)
		txt=""
		if len(msgids)==0:
			txt=u'Новых сообщений нет.'
		else:
			txt+=u'Новые сообщения:'
			for msgid in msgids:
				arr=getMsg(msgid)
				txt+="\n\n"+arr.get('echo')+"\nmsgid: "+arr.get('id')+"\n"+formatDate(arr.get('time'))+"\n"+arr.get('subj')+"\n"+arr.get('sender')+" -> "+arr.get('to')+"\n\n"+arr.get('msg')
		self.textEdit.setText(txt)

app = QtGui.QApplication(sys.argv)
form=Form()
form.show()
app.exec_()
