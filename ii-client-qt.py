#!/usr/bin/env python3

import locale,sys
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

from getcfg import *
from ii_functions import *
import webfetch
import writemsg
import sender
import re
import webbrowser
from threading import Thread
import ctypes
import queue

from PyQt5 import QtCore, QtGui, QtWidgets, uic

urltemplate=re.compile("(https?|ftp|file)://?[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]")
quotetemplate=re.compile(r"^\s?[\w_А-Яа-я\-]{0,20}(&gt;)+.+$", re.MULTILINE | re.IGNORECASE)
commenttemplate=re.compile(r"(^|\s+)(PS|P\.S|ЗЫ|З\.Ы|\/\/|#).+$", re.MULTILINE | re.IGNORECASE)
ii_link=re.compile(r"ii:\/\/(\w[\w.]+\w+)", re.MULTILINE)

def updatemsg():
	global msgnumber,msgid_answer,msglist
	msgid_answer=msglist[msgnumber]
	msg=getMsgEscape(msgid_answer)
	
	repto1=msg.get('repto')

	if(repto1):
		repto=repto1
	else:
		repto="-"

	msgtext="msgid: "+msgid_answer+"<br />"+"Ответ на: "+repto+"<br />"+formatDate(msg.get('time'))+"<br />"+msg.get('subj')+"<br /><b>"+msg.get('sender')+" ("+msg.get('addr')+")  ->  "+msg.get('to')+"</b><br />"

	form.listWidget.setCurrentRow(msgnumber)
	form.textBrowser.setHtml(msgtext+"<br />"+reparseMessage(msg.get('msg')))

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
	global msgnumber
	msgnumber=form.listWidget.currentRow()
	updatemsg()

def c_writeNew(event):
	global echo
	writemsg.writeNew(echo)

def sendWrote_operation():
	countsent=0
	try:
		countsent=sender.sendMessages()
	except stoppedDownloadException as e:
		form.newmsgq.put(e)
		return
	except Exception as e:
		form.newmsgq.put(e)
		form.errorsq.put(["Ошибка отправки: ", e])
		return
	form.newmsgq.put(countsent)
	
def sendWrote(event):
	result=form.processNewThread(sendWrote_operation)

	if (not isinstance(result, Exception)):
		form.mbox.setText("Отправлено сообщений: "+str(result))
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
	global urltemplate, quotetemplate, commenttemplate, ii_link
	string=urltemplate.sub("<a href='\g<0>'>\g<0></a>", string)
	string=quotetemplate.sub("<font color='green'>\g<0></font>", string)
	string=commenttemplate.sub("<font color='brown'>\g<0></font>", string)
	string=ii_link.sub("<a href='#\g<1>'>\g<0></a>", string)

	strings=string.splitlines()
	pre_flag=False

	for i in range(0, len(strings)):
		if strings[i]=="====":
			if not pre_flag:
				pre_flag=True
				strings[i]="<pre style='font-family: monospace;'>===="
			else:
				pre_flag=False
				strings[i]="====</pre>"
	
	return "<br />".join(strings)

def openLink(link):
	global ii_link
	link=link.toString()
	
	if (link.startswith("#")): # если перед нами ii-ссылка
		link=link[1:] # срезаем первые ненужные символы
		if "." in link:
			form.viewwindow(link) # переходим в эху
		else:
			form.openMessageView(link) # смотрим сообщение
	else:
		print("opening link in default browser")
		webbrowser.open(link)

class Form(QtWidgets.QMainWindow):
	def __init__(self):
		global msglist,msgnumber,listlen
		super(Form, self).__init__()

		windowIcon=QtGui.QIcon('artwork/iilogo.png')

		self.newmsgq=queue.Queue()
		self.errorsq=queue.Queue()
		self.loadviewq=queue.Queue()

		self.networkingThread=Thread()
		self.loadViewThread=Thread()

		self.setWindowIcon(windowIcon)
		self.mbox=QtWidgets.QMessageBox()
		self.mbox.setText("")

		self.progress=QtWidgets.QProgressDialog(self)
		self.progress.setLabel(QtWidgets.QLabel("Подгружаем эху..."))
		self.progress.hide()

		# настраиваем диалог удаления тоссов

		self.clearMessages=QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, "Подтверждение", "Удалить исходящие сообщения?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
		self.deleteAll=QtWidgets.QCheckBox("В том числе отправленные")
		self.clearMessages.setCheckBox(self.deleteAll)

		self.clearXC=QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, "Подтверждение", "Удалить данные /x/c?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

		self.setupClientConfig()
		self.setupServersConfig()
		self.setupMenu()
		self.setupHelp()

		# если запускаем клиент в первый раз, сначала показываются настройки
		if (config["firstrun"]==True):
			config["firstrun"]=False
			self.execServersConfig()
			if not config["autoSaveChanges"]:
				self.saveChanges()
		
		self.mainwindow()

	def mainwindow(self):
		setUIResize("qtgui-files/mainwindow.ui",self)

		self.pushButton.clicked.connect(self.getNewText)
		self.pushButton_2.clicked.connect(sendWrote)
		self.pushButton_3.clicked.connect(self.displayOfflineEchos)
		self.pushButton_4.clicked.connect(self.updateMainView)
		self.menuButton.setMenu(self.clMenu)

		for server in servers:
			self.comboBox.addItem(server["adress"])
		
		self.comboBox.currentIndexChanged.connect(self.loadEchoList)
		self.listWidget.itemActivated.connect(self.openViewWindow)
		self.loadEchoList()
		
	def viewwindow(self, echoarea):
		global msglist,msgnumber,listlen,echo
		echo=echoarea
		msgnumber=0

		setUIResize("qtgui-files/viewwindow.ui",self)

		self.setWindowTitle("Просмотр сообщений: "+echoarea)

		msglist=getMsgList(echo)
		msglist.reverse()

		listlen=len(msglist)

		self.progress.setMaximum(listlen-1)
		self.processProgressBar(self.loadEchoBase)

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
	
	def processNewThread(self, function):
		if self.networkingThread.isAlive():
			return

		debugform.show()
		self.hide()

		self.networkingThread=Thread(target=function)
		self.networkingThread.daemon=True
		self.networkingThread.start()

		while (self.networkingThread.isAlive()):
			if (not gprintq.empty()):
				debugform.addText(gprintq.get())
			app.processEvents()
		
		while (not self.errorsq.empty()):
			error=self.errorsq.get()
			self.mbox.setText(error[0]+'\n\n'+str(error[1]))
			self.mbox.exec_()

		self.networkingThread.join()
		
		debugform.close()
		self.show()
		return self.newmsgq.get()

	def loadEchoBase(self):
		global msglist, listlen
		with self.loadviewq.mutex:
			self.loadviewq.queue.clear()

		for i in range(listlen):
			self.loadviewq.put_nowait([i,getMsgEscape(msglist[i]).get('subj')])

	def processProgressBar(self, function):
		self.setVisible(0)
		self.progress.show()

		self.loadViewThread=Thread(target=function)
		self.loadViewThread.daemon=True
		self.loadViewThread.start()

		while True:
			app.processEvents()

			if (not self.loadviewq.empty() or self.loadViewThread.isAlive()):
				element=self.loadviewq.get()
				self.listWidget.addItem(element[1]) # это сабж вообще-то
				self.progress.setValue(element[0]) # а это - значение прогрессбара
			else:
				break

		self.loadViewThread.join()
		self.setVisible(1)
		self.progress.hide()

	def getNewMessages(self):
		msgids=[]
		
		for server in servers:
			try:
				if (not "advancedue" in server.keys()): # проверяем, если конфиг старый
					server["advancedue"]=False

				if (server["advancedue"] == False):
					uelimit=False
				else:
					uelimit=server["uelimit"]
					# uelimit - сколько msgid скачивать максимум при наличии расширенной схемы
					# если стоит в False, то скачиваем все

				msgidsNew=webfetch.fetch_messages(server["adress"], server["echoareas"], server["xcenable"], fetch_limit=uelimit)
				msgids+=msgidsNew
			except stoppedDownloadException:
				break
			except Exception as e:
				self.errorsq.put([server["adress"]+": ошибка получения сообщений (проблемы с интернетом?)", e])

		self.newmsgq.put(msgids)
	
	def getNewText(self):
		msgids=self.processNewThread(self.getNewMessages)
		
		if len(msgids)==0:
			self.mbox.setText('Новых сообщений нет.')
			self.mbox.exec_()
		else:
			self.getDialog()
			htmlcode="Новые сообщения:"
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
					print("rm "+filename)
					counter+=1
					os.remove(os.path.join(paths.tossesdir, filename))
			else:
				for filename in os.listdir(paths.tossesdir):
					if filename[-5:]==".toss":
						print("rm "+filename)
						counter+=1
						os.remove(os.path.join(paths.tossesdir, filename))
			
			if counter>0:
				self.mbox.setText("Удалено сообщений: "+str(counter))
			else:
				self.mbox.setText("Удалять нечего")
			self.mbox.exec_()

	def deleteXC(self):
		answer=self.clearXC.exec_()
		counter=0

		if answer == QtWidgets.QMessageBox.Yes:
			for filename in os.listdir(paths.datadir):
				if filename[:5]=="base-":
					print("rm "+filename)
					counter+=1
					os.remove(os.path.join(paths.datadir, filename))
			
			if counter>0:
				self.mbox.setText("Удалено файлов: "+str(counter))
			else:
				self.mbox.setText("Удалять нечего")
			self.mbox.exec_()

	def setupMenu(self):
		self.clMenu=QtWidgets.QMenu()

		clientSettingsAction=QtWidgets.QAction("Настройки клиента", self)
		serversSettingsAction=QtWidgets.QAction("Настройки станций", self)
		saveSettingsAction=QtWidgets.QAction("Сохранить настройки", self)
		deleteTossesAction=QtWidgets.QAction("Удалить исходящие", self)
		deleteXCAction=QtWidgets.QAction("Удалить данные /x/c", self)
		helpAction=QtWidgets.QAction("Справка", self)
		
		clientSettingsAction.triggered.connect(self.execClientConfig)
		serversSettingsAction.triggered.connect(self.execServersConfig)
		saveSettingsAction.triggered.connect(self.saveChanges)
		deleteTossesAction.triggered.connect(self.deleteTosses)
		deleteXCAction.triggered.connect(self.deleteXC)
		helpAction.triggered.connect(self.showHelp)

		self.clMenu.addAction(clientSettingsAction)
		self.clMenu.addAction(serversSettingsAction)
		self.clMenu.addAction(saveSettingsAction)
		
		self.clMenu.addSeparator()
		self.clMenu.addAction(deleteTossesAction)
		self.clMenu.addAction(deleteXCAction)

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
		self.serversConfig.checkBox_2.stateChanged.connect(self.changeSpinBox)
	
	def loadInfo_client(self):
		self.clientConfig.lineEdit.setText(config["editor"])
		self.clientConfig.listWidget.clear()
		self.clientConfig.listWidget.addItems(config["offline-echoareas"])

		if (len(config["offline-echoareas"])>0):
			self.clientConfig.listWidget.setCurrentRow(0)
		
		self.clientConfig.checkBox.setChecked(config["defaultEditor"])
		self.clientConfig.checkBox_2.setChecked(config["firstrun"])
		self.clientConfig.checkBox_3.setChecked(config["autoSaveChanges"])

	def loadInfo_servers(self, index=0):
		curr=servers[index]

		self.serversConfig.lineEdit.setText(curr["adress"])
		self.serversConfig.lineEdit_2.setText(curr["authstr"])
		self.serversConfig.listWidget.clear()
		self.serversConfig.listWidget.addItems(curr["echoareas"])

		if (len(curr["echoareas"])>0):
			self.serversConfig.listWidget.setCurrentRow(0)

		if (not "advancedue" in curr.keys()):
			curr["advancedue"]=False
			curr["uelimit"]=100

		self.serversConfig.checkBox.setChecked(curr["xcenable"])
		self.serversConfig.checkBox_2.setChecked(curr["advancedue"])
		self.serversConfig.spinBox.setValue(curr["uelimit"])
	
	def loadEchoList(self, index=0):
		self.listWidget.clear()
		self.listWidget.addItems(servers[index]["echoareas"])
	
	def updateMainView(self):
		self.listWidget.clear()
		index=self.comboBox.currentIndex()
		self.listWidget.addItems(servers[index]["echoareas"])
		
		self.comboBox.clear()
		for server in servers:
			self.comboBox.addItem(server["adress"])
	
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
		config["defaultEditor"]=self.clientConfig.checkBox.isChecked()
		config["firstrun"]=self.clientConfig.checkBox_2.isChecked()
		config["autoSaveChanges"]=self.clientConfig.checkBox_3.isChecked()
		count=self.clientConfig.listWidget.count()

		config["offline-echoareas"]=[]

		for index in range(0,count):
			config["offline-echoareas"].append(self.clientConfig.listWidget.item(index).text())

		self.saveOrNot()
	
	def applyServersConfig(self, index=0):
		servers[index]["adress"]=self.serversConfig.lineEdit.text()
		servers[index]["authstr"]=self.serversConfig.lineEdit_2.text()
		servers[index]["xcenable"]=self.serversConfig.checkBox.isChecked()
		servers[index]["advancedue"]=self.serversConfig.checkBox_2.isChecked()
		servers[index]["uelimit"]=self.serversConfig.spinBox.value()

		servers[index]["echoareas"]=[]
		count=self.serversConfig.listWidget.count()
		
		for itemNumber in range(0,count):
			servers[index]["echoareas"].append(self.serversConfig.listWidget.item(itemNumber).text())

		config["servers"]=servers
		
		self.saveOrNot()
	
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
	
	def saveOrNot(self): # смотрим, стоит ли автосохранение настроек
		# если стоит, то сохраняем их
		if config["autoSaveChanges"]:
			self.saveChanges()

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
		servers.append({"authstr":"", "adress":"http://your-station.ru/", "xcenable":False, "echoareas":[]})
		newindex=self.serversConfig.tabBar.addTab(str(len(servers)))
		self.serversConfig.tabBar.setCurrentIndex(newindex)
	
	def changeSpinBox(self, state):
		if (state == 0):
			self.serversConfig.spinBox.setReadOnly(True)
		else:
			self.serversConfig.spinBox.setReadOnly(False)
	
	def tabDeleteRequest(self):
		currindex=self.serversConfig.tabBar.currentIndex()
		self.serversConfig.tabBar.removeTab(currindex)
		del servers[currindex]
		self.loadInfo_servers(self.serversConfig.tabBar.currentIndex())
	
	def openViewWindow(self, item):
		echoarea=item.text()
		self.viewwindow(echoarea)
	
	def displayOfflineEchos(self):
		self.listWidget.clear()
		
		if len(config["offline-echoareas"]) > 0:
			self.listWidget.addItems(config["offline-echoareas"])
	
	def openMessageView(self, msgid):
		global echo, msgid_answer # сохраняем msgid исходной эхи, чтобы
		tmpecho=str(echo) # можно было бы отвечать на сообщения
		tmpmsgid=str(msgid_answer) # после закрытия диалога

		msg=getMsgEscape(msgid)
		
		repto1=msg.get('repto')

		if(repto1):
			repto=repto1
		else:
			repto="-"
		
		msgtext="msgid: "+msgid+"<br />"+"Ответ на: "+repto+"<br />"+formatDate(msg.get('time'))+"<br />"+msg.get('subj')+"<br /><b>"+msg.get('sender')+" ("+msg.get('addr')+")  ->  "+msg.get('to')+"</b><br />"

		msgid_answer=msgid # меняем глобальный msgid для
		echo=msg.get('echo') # возможности ответить на сообщение

		dialog=QtWidgets.QDialog(self)
		uic.loadUi("qtgui-files/viewmessage.ui", dialog)
		dialog.textBrowser.setHtml(msgtext+"<br />"+reparseMessage(msg.get('msg')))
		dialog.textBrowser.anchorClicked.connect(openLink)
		dialog.AnswerButton.clicked.connect(answer)
		dialog.exec_()

		msgid_answer=tmpmsgid # возвращаем всё на свои места
		echo=tmpecho

		dialog.destroy()

class debugForm(QtWidgets.QDialog):
	def __init__(self):
		super(debugForm, self).__init__()
		setUIResize("qtgui-files/debugview.ui",self)
		self.pushButton.clicked.connect(self.user_stop)
	
	def user_stop(self):
		ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(form.networkingThread.ident),ctypes.py_object(stoppedDownloadException))
	
	def addText(sender, text):
		debugform.textBrowser.append(text)

	def closeEvent(self, event):
		self.textBrowser.clear()
		self.hide()
		event.ignore()

def my_print(func): # декоратор над стандартным питоновским print'ом
	def wrapper(arg):
		gprintq.put(arg)
		func(arg)
	return wrapper

gprintq=queue.Queue()
print=my_print(print) # теперь print - это уже не print =)
webfetch.print=print
sender.print=print

class stoppedDownloadException(Exception):
	def __init__(self):
		super(stoppedDownloadException, self).__init__("Скачивание остановлено")

app = QtWidgets.QApplication(sys.argv)

form=Form()
debugform=debugForm()

form.show()
sys.exit(app.exec_())
