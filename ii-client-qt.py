#!/usr/bin/env python2
# -*- coding:utf8 -*-
import locale,sys
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

from getcfg import *
from ii_functions import *
import webfetch
import writemsg
import sender
import re
import webbrowser

from PyQt5 import QtCore, QtGui, QtWidgets, uic

urltemplate=re.compile("(https?|ftp|file)://?[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]")
quotetemplate=re.compile("^&gt;+.+$", re.MULTILINE)

def updatemsg():
	global msgnumber,msgid_answer,slf,msglist
	msgid_answer=msglist[msgnumber]
	msg=getMsgEscape(msgid_answer)
	
	repto1=msg.get('repto')

	if(repto1):
		repto=repto1
	else:
		repto=u"-"

	msgtext="msgid: "+msgid_answer+"<br />"+u"Ответ на: "+repto+"<br />"+formatDate(msg.get('time'))+"<br />"+msg.get('subj')+"<br /><b>"+msg.get('sender')+" ("+msg.get('addr')+")  ->  "+msg.get('to')+"</b><br />"

	slf.listWidget.setCurrentRow(msgnumber)
	slf.textBrowser.setHtml(msgtext+"<br />"+reparseMessage(msg.get('msg')))

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
	try:
		countsent=sender.sendMessages()
		form.mbox.setText(u"Отправлено сообщений: "+str(countsent))
		form.mbox.exec_()
	except Exception,e:
		form.mbox.setText(u"Ошибка отправки: "+str(e).decode("utf8"))
		form.mbox.exec_()

def answer(event):
	global echo,msgid_answer
	writemsg.answer(echo, msgid_answer)

def setUIResize(filename, object):
	# данный метод чинит изменение размера окна
	# в тайловых оконных менеджерах
	# в qt4 это не нужно было, а в 5 нужно
	currentsize=object.size()
	uic.loadUi(filename,object)
	object.resize(currentsize) # восстанавливаем предыдущий размер

def reparseMessage(string):
	global urltemplate, quotetemplate
	string=urltemplate.sub(u"<a href='\g<0>'>\g<0></a>", string)
	string=quotetemplate.sub(u"<font color='green'>\g<0></font>", string)
	return string.replace("\n", "<br />")

def openLink(link):
	print "opening link in default browser"
	webbrowser.open(link.toString())

class Form(QtWidgets.QMainWindow):
	def __init__(self):
		super(Form, self).__init__()

		windowIcon=QtGui.QIcon('artwork/iilogo.png')
		self.setWindowIcon(windowIcon)

		self.resize(400,500)
		self.mainwindow()
		global slf,msglist,msgnumber,listlen
		slf=self
		self.mbox=QtWidgets.QMessageBox()
		self.mbox.setText(u"")

		# настраиваем диалог удаления тоссов

		self.clearMessages=QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, u"Подтверждение", u"Удалить исходящие сообщения", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
		self.clearMessages.setText(u"Удалить исходящие сообщения?")
		self.deleteAll=QtWidgets.QCheckBox(u"В том числе отправленные")
		self.clearMessages.setCheckBox(self.deleteAll)

	def exc(self,cmd):
		exec compile(cmd, "<string>", "exec")

	def mainwindow(self):
		setUIResize("qtgui-files/mainwindow.ui",self)

		self.pushButton.clicked.connect(self.getNewText)
		self.pushButton_2.clicked.connect(sendWrote)
		self.deleteTossesButton.clicked.connect(self.deleteTosses)

		def addButtons(echoareas):
			for i in range(0,len(echoareas)):
				cmd="self.but"""+str(i)+"=QtWidgets.QPushButton('"+echoareas[i]+"',self)"+"""
def callb"""+str(i)+"(event):"+"""
	slf.viewwindow('"""+echoareas[i]+"""')
self.but"""+str(i)+".setFlat(True)"+"""
self.but"""+str(i)+".clicked.connect(callb"+str(i)+""")
self.verticalLayout.addWidget(self.but"""+str(i)+")"
				self.exc(cmd)

		for server in servers:
			echoareas=server["echoareas"]
			self.verticalLayout.addWidget(QtWidgets.QLabel(server["adress"], self))
			addButtons(server["echoareas"])
		
		if(len(config["offline-echoareas"])>0):
			self.verticalLayout.addWidget(QtWidgets.QLabel(u"Эхи без сервера", self))
			addButtons(config["offline-echoareas"])

	def viewwindow(self, echoarea):
		global msglist,msgnumber,listlen,echo
		echo=echoarea

		setUIResize("qtgui-files/viewwindow.ui",self)

		self.setWindowTitle(u"Просмотр сообщений: "+echoarea)
	
		msglist=getMsgList(echoarea)
		msglist.reverse()

		msgnumber=0
		listlen=len(msglist)-2

		for i in range(listlen+2):
			self.listWidget.addItem(getMsgEscape(msglist[i]).get('subj'))

		self.listWidget.currentRowChanged.connect(lbselect)
		self.listWidget.setCurrentRow(msgnumber)

		self.pushButton.clicked.connect(self.mainwindow)
		self.pushButton_2.clicked.connect(msgminus)
		self.pushButton_3.clicked.connect(msgplus)
		self.pushButton_4.clicked.connect(sendWrote)
		self.pushButton_5.clicked.connect(answer)
		self.pushButton_6.clicked.connect(c_writeNew)
		self.pushButton_7.clicked.connect(self.getNewText)

		self.deleteTossesButton.clicked.connect(self.deleteTosses)
		self.textBrowser.anchorClicked.connect(openLink)

	def getDialog(self):
		setUIResize("qtgui-files/getwindow.ui",self)

		self.pushButton.clicked.connect(self.getNewText)
		self.pushButton_2.clicked.connect(self.mainwindow)
		self.textBrowser.anchorClicked.connect(openLink)
	
	def getNewText(self):
		msgids=[]
		
		for server in servers:
			try:
				msgidsNew=webfetch.fetch_messages(server["adress"], server["echoareas"], server["xtenable"])
				msgids+=msgidsNew
			except Exception, e:
				self.mbox.setText(server["adress"]+u': ошибка получения сообщений (проблемы с интернетом?).\n\n'+str(e).decode("utf8"))
				self.mbox.exec_()
		
		if len(msgids)==0:
			self.mbox.setText(u'Новых сообщений нет.')
			self.mbox.exec_()
		else:
			self.getDialog()
			htmlcode=u"Новые сообщения:"
			for msgid in msgids:
				arr=getMsgEscape(msgid)
				htmlcode+="<br /><br />"+arr.get('echo')+"<br />msgid: "+arr.get('id')+"<br />"+formatDate(arr.get('time'))+"<br />"+arr.get('subj')+"<br /><b>"+arr.get('sender')+' ('+arr.get('addr')+') -> '+arr.get('to')+"</b><br /><br />"+reparseMessage(arr.get('msg'))
			self.textBrowser.insertHtml(htmlcode)
	
	def deleteTosses(self):
		answer=self.clearMessages.exec_()
		counter=0

		if answer == QtWidgets.QMessageBox.Yes:
			if self.deleteAll.isChecked():
				for filename in os.listdir(paths.tossesdir):
					print "rm "+filename
					counter+=1
					os.remove(os.path.join(paths.tossesdir, filename))
			else:
				for filename in os.listdir(paths.tossesdir):
					if filename[-5:]==".toss":
						print "rm "+filename
						counter+=1
						os.remove(os.path.join(paths.tossesdir, filename))
			
			if counter>0:
				self.mbox.setText(u"Удалено сообщений: "+str(counter))
			else:
				self.mbox.setText(u"Удалять нечего")
			self.mbox.exec_()

app = QtWidgets.QApplication(sys.argv)
form=Form()
form.show()
sys.exit(app.exec_())
