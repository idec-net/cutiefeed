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

def editItem(event):
	lw=event.listWidget()
	event.setFlags(QtCore.Qt.ItemFlags(1|2|32)) # ставим, что элемент активный, что его можно править, и что он выбираемый
	lw.editItem(event)

def deleteItem(event):
	form.currLw.takeItem(form.currLw.currentRow())

def addItem(event):
	newListItem=QtWidgets.QListWidgetItem("echoarea.15")
	newListItem.setFlags(QtCore.Qt.ItemFlags(1|2|32))
	targetRow=form.currLw.currentRow()+1
	form.currLw.insertItem(targetRow, newListItem)
	form.currLw.setCurrentRow(targetRow)
	form.currLw.editItem(newListItem)

def itemUp(event):
	targetRow=form.currLw.currentRow()-1
	if (targetRow>=0):
		tookItem=form.currLw.takeItem(targetRow+1)
		form.currLw.insertItem(targetRow, tookItem)
		form.currLw.setCurrentRow(targetRow)

def itemDown(event):
	targetRow=form.currLw.currentRow()+1
	count=form.currLw.count()
	if (targetRow<count):
		tookItem=form.currLw.takeItem(targetRow-1)
		form.currLw.insertItem(targetRow, tookItem)
		form.currLw.setCurrentRow(targetRow)

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
		global slf,msglist,msgnumber,listlen
		slf=self
		self.mbox=QtWidgets.QMessageBox()
		self.mbox.setText(u"")

		# настраиваем диалог удаления тоссов

		self.clearMessages=QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, u"Подтверждение", u"Удалить исходящие сообщения?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
		self.deleteAll=QtWidgets.QCheckBox(u"В том числе отправленные")
		self.clearMessages.setCheckBox(self.deleteAll)

		self.clearXT=QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, u"Подтверждение", u"Удалить данные /x/t?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

		self.setupClientConfig()
		self.setupServersConfig()
		self.setupMenu()
		self.setupHelp()
		self.mainwindow()

	def exc(self,cmd):
		exec compile(cmd, "<string>", "exec")

	def mainwindow(self):
		setUIResize("qtgui-files/mainwindow.ui",self)

		self.pushButton.clicked.connect(self.getNewText)
		self.pushButton_2.clicked.connect(sendWrote)
		self.menuButton.setMenu(self.clMenu)

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

		self.menuButton.setMenu(self.clMenu)
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

	def deleteXT(self):
		answer=self.clearXT.exec_()
		counter=0

		if answer == QtWidgets.QMessageBox.Yes:
			for filename in os.listdir(paths.datadir):
				if filename[:5]=="base-":
					print "rm "+filename
					counter+=1
					os.remove(os.path.join(paths.datadir, filename))
			
			if counter>0:
				self.mbox.setText(u"Удалено файлов: "+str(counter))
			else:
				self.mbox.setText(u"Удалять нечего")
			self.mbox.exec_()

	def setupMenu(self):
		self.clMenu=QtWidgets.QMenu()

		clientSettingsAction=QtWidgets.QAction("Настройки клиента", self)
		serversSettingsAction=QtWidgets.QAction("Настройки станций", self)
		saveSettingsAction=QtWidgets.QAction("Сохранить настройки", self)
		deleteTossesAction=QtWidgets.QAction("Удалить исходящие", self)
		deleteXTAction=QtWidgets.QAction("Удалить данные /x/t", self)
		helpAction=QtWidgets.QAction("Справка", self)
		
		clientSettingsAction.triggered.connect(self.execClientConfig)
		serversSettingsAction.triggered.connect(self.execServersConfig)
		saveSettingsAction.triggered.connect(self.saveChanges)
		deleteTossesAction.triggered.connect(self.deleteTosses)
		deleteXTAction.triggered.connect(self.deleteXT)
		helpAction.triggered.connect(self.showHelp)

		self.clMenu.addAction(clientSettingsAction)
		self.clMenu.addAction(serversSettingsAction)
		self.clMenu.addAction(saveSettingsAction)
		
		self.clMenu.addSeparator()
		self.clMenu.addAction(deleteTossesAction)
		self.clMenu.addAction(deleteXTAction)

		self.clMenu.addSeparator()
		self.clMenu.addAction(helpAction)

	def setupClientConfig(self):
		self.clientConfig=uic.loadUi("qtgui-files/clientconfig.ui")
		self.clientConfig.listWidget.itemDoubleClicked.connect(editItem)
		self.clientConfig.pushButton.clicked.connect(addItem) # кнопка Добавить
		self.clientConfig.pushButton_2.clicked.connect(deleteItem) # кнопка Удалить
		self.clientConfig.pushButton_3.clicked.connect(itemUp) # кнопка Вверх
		self.clientConfig.pushButton_4.clicked.connect(itemDown) # кнопка Вниз

		self.clientConfig.accepted.connect(self.applyClientConfig)

	def setupServersConfig(self):
		self.serversConfig=uic.loadUi("qtgui-files/stations.ui")

		self.serversConfig.tabBar=QtWidgets.QTabBar(self.serversConfig)
		self.serversConfig.tabBar.setMovable(True)

		self.serversConfig.horizontalLayout.addWidget(self.serversConfig.tabBar)
		self.serversConfig.horizontalLayout.addWidget(self.serversConfig.addTabButton)
		self.serversConfig.horizontalLayout.addWidget(self.serversConfig.deleteTabButton)

		for i in range(len(servers)):
			self.serversConfig.tabBar.addTab(str(i+1))

		self.oldCurrentTab=0
		self.serversConfig.tabBar.currentChanged.connect(self.updateInfo_servers_fromTab)
		self.serversConfig.tabBar.tabMoved.connect(self.tabMovedEvent)

		self.serversConfig.listWidget.itemDoubleClicked.connect(editItem)
		self.serversConfig.pushButton.clicked.connect(addItem) # кнопка Добавить
		self.serversConfig.pushButton_2.clicked.connect(deleteItem) # кнопка Удалить
		self.serversConfig.pushButton_3.clicked.connect(itemUp) # кнопка Вверх
		self.serversConfig.pushButton_4.clicked.connect(itemDown) # кнопка Вниз

		self.serversConfig.addTabButton.clicked.connect(self.tabAddRequest)
		self.serversConfig.deleteTabButton.clicked.connect(self.tabDeleteRequest)

		self.serversConfig.accepted.connect(self.applyServersConfigFromButton)
	
	def loadInfo_client(self):
		self.clientConfig.lineEdit.setText(config["editor"])
		self.clientConfig.listWidget.clear()
		self.clientConfig.listWidget.addItems(config["offline-echoareas"])

		if (len(config["offline-echoareas"])>0):
			self.clientConfig.listWidget.setCurrentRow(0)

	def loadInfo_servers(self, index=0):
		curr=servers[index]

		self.serversConfig.lineEdit.setText(curr["adress"])
		self.serversConfig.lineEdit_2.setText(curr["authstr"])
		self.serversConfig.listWidget.clear()
		self.serversConfig.listWidget.addItems(curr["echoareas"])

		if (len(curr["echoareas"])>0):
			self.serversConfig.listWidget.setCurrentRow(0)

		checkState=0

		if curr["xtenable"]==True:
			checkState=2 # ставим, что чекбокс нажат

		self.serversConfig.checkBox.setCheckState(checkState)
	
	def execClientConfig(self):
		self.loadInfo_client()
		self.currLw=self.clientConfig.listWidget
		self.clientConfig.exec_()
	
	def execServersConfig(self):
		self.serversConfig.tabBar.setCurrentIndex(0)
		self.loadInfo_servers(0)
		self.oldCurrentTab=0
		self.currLw=self.serversConfig.listWidget

		for i in range(len(servers)):
			self.serversConfig.tabBar.setTabText(i, str(i+1))
		
		self.serversConfig.exec_()
	
	def applyClientConfig(self):
		config["editor"]=self.clientConfig.lineEdit.text()
		count=self.clientConfig.listWidget.count()

		config["offline-echoareas"]=[]

		for index in range(0,count):
			config["offline-echoareas"].append(self.clientConfig.listWidget.item(index).text())
	
	def applyServersConfig(self, index=0):
		servers[index]["adress"]=self.serversConfig.lineEdit.text()
		servers[index]["authstr"]=self.serversConfig.lineEdit_2.text()
		servers[index]["xtenable"]=self.serversConfig.checkBox.isChecked()

		servers[index]["echoareas"]=[]
		count=self.serversConfig.listWidget.count()
		
		for itemNumber in range(0,count):
			servers[index]["echoareas"].append(self.serversConfig.listWidget.item(itemNumber).text())

		config["servers"]=servers
	
	def applyServersConfigFromButton(self):
		curr=self.serversConfig.tabBar.currentIndex()
		self.applyServersConfig(curr)

	def updateInfo_servers_fromTab(self, index=0):
		self.applyServersConfig(self.oldCurrentTab)
		self.oldCurrentTab=index
		self.loadInfo_servers(index)

	def saveChanges(self):
		result=saveConfig()
		if result:
			self.mbox.setText("Настройки сохранены")
		else:
			self.mbox.setText("Упс, сохранить не получилось, смотри в логи.")
		return self.mbox.exec_()
	
	def setupHelp(self):
		helpfile=open("readme.html").read()
		self.helpWindow=uic.loadUi("qtgui-files/readhelp.ui")
		self.helpWindow.textBrowser.setHtml(helpfile)

		pm1=QtGui.QPixmap("artwork/iilogo.png")
		self.pm2=QtGui.QPixmap("artwork/iipony.png")
		self.helpWindow.label_2.setPixmap(pm1)
		self.helpWindow.label_2.mouseReleaseEvent = self.setnext

		self.helpWindow.textBrowser.anchorClicked.connect(openLink)

	def showHelp(self):
		self.helpWindow.show()
	
	def setnext(self,e):
		self.helpWindow.label_2.setPixmap(self.pm2)
	
	def tabMovedEvent(self, first, second):
		servers[first], servers[second] = servers[second], servers[first]
		self.oldCurrentTab=self.serversConfig.tabBar.currentIndex()
	
	def tabAddRequest(self):
		servers.append({"authstr":"", "adress":"http://your-station.ru/", "xtenable":False, "echoareas":[]})
		newindex=self.serversConfig.tabBar.addTab(str(len(servers)))
		self.serversConfig.tabBar.setCurrentIndex(newindex)
	
	def tabDeleteRequest(self):
		currindex=self.serversConfig.tabBar.currentIndex()
		self.serversConfig.tabBar.removeTab(currindex)
		del servers[currindex]
		self.loadInfo_servers(self.serversConfig.tabBar.currentIndex())

app = QtWidgets.QApplication(sys.argv)
form=Form()
form.show()
sys.exit(app.exec_())
