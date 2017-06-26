#!/usr/bin/env python3

from PyQt5 import QtCore, QtGui, QtWidgets, uic

import sys
from getcfg import *
from ii_functions import *
import network
import webfetch
import writemsg
import sender
import re
import webbrowser
from threading import Thread
import ctypes
import queue
import json, shutil, math, uuid
import urllib.parse

urltemplate=re.compile("(https?|ftp|file)://?[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]")
quotetemplate=re.compile(r"^\s?[\w_А-Яа-я\-]{0,20}(&gt;)+.+$", re.MULTILINE | re.IGNORECASE)
commenttemplate=re.compile(r"(^|(\w\s+))(PS|P\.S|ЗЫ|З\.Ы|\/\/|#)(.+$)", re.MULTILINE | re.IGNORECASE)
ii_link=re.compile(r"ii:\/\/(\w[\w.-]+\w+)", re.MULTILINE)

def get_favorites():
	try:
		f=open(paths.favoritesfile)
		storage=json.load(f)
		f.close()
		return storage
	except:
		return {"list":[], "subjes":{}}

def save_favorites(array):
	try:
		f=open(paths.favoritesfile, "w")
		json.dump(array, f)
		f.close()
	except Exception as e:
		print("Ошибка сохранения списка избранных сообщений: "+str(e))

def outbox_id_by_address(addr):
	for server in config["servers"]:
		if server["adress"] == addr:
			return server["outbox_storage_id"]
	return None

def outbox_id_by_echoarea(echoarea):
	for server in config["servers"]:
		if echoarea in server:
			return server["outbox_storage_id"]
	return None

def getproxy():
	proxy=None
	if config["useProxy"]:
		proxy={config["proxyType"]: config["proxy"]}
	return proxy

def get_pos_cache():
	try:
		f=open(paths.echopositionfile)
		pos_cache=json.load(f)
		f.close()
		return pos_cache
	except:
		return {}

def get_position(echo, cache):
	if not echo in cache.keys():
		return None
	else:
		return cache[echo]

def save_pos_cache(cache):
	try:
		f=open(paths.echopositionfile, "w")
		json.dump(cache, f)
		f.close()
	except Exception as e:
		print("Ошибка сохранения кэша позиции: "+str(e))

def get_subj_cache(echo):
	filename=os.path.join(paths.subjcachedir, echo)
	try:
		cache=read_file(filename).splitlines()
		return cache
	except:
		touch(filename)
		return []

def cache_exists(echo):
	filename=os.path.join(paths.subjcachedir, echo)
	return os.path.exists(filename)

def append_subj_cache(subj_data, echo):
	if type(subj_data) == list:
		subj_data="\n".join(subj_data)
	try:
		filename=os.path.join(paths.subjcachedir, echo)
		f=open(filename, "a")
		f.write(subj_data+"\n")
		f.close()
		return True
	except:
		print("error append cache")
		return False

def load_raw_file(adress, data=None):
	def loadFunction():
		try:
			string=network.getfile(adress, getproxy(), data, timeout=config["connectionTimeout"])
			form.newmsgq.put(string)
		except Exception as e:
			form.errorsq.put(["Ошибка скачивания: ", e])
			form.newmsgq.put("")

	return form.processNewThread(loadFunction)

def prettier_size(n,pow=0,b=1024,u='B',pre=['']+[p+'i'for p in'KMGTPEZY']):
	r,f=min(int(math.log(max(n*b**pow,1),b)),len(pre)-1),'{:,.%if} %s%s'
	return (f%(abs(r%(-r-1)),pre[r],u)).format(n*b**pow/b**float(r))

def xfile_download(server, filename, savename, signal):
	data = urllib.parse.urlencode({'pauth': server["authstr"], 'filename':filename}).encode('utf8')
	try:
		out = network.getfile(server["adress"] + 'x/file', getproxy(), data, return_descriptor=True, timeout=config["connectionTimeout"])
	except Exception as e:
		form.errorsq.put(["Ошибка скачивания: ", e])
		form.newmsgq.put("Ну не получилось, чего поделаешь!")
		return

	file_size=0
	block_size=8192

	f=open(savename, "wb")
	while True:
		buffer=out.read(block_size)
		if not buffer:
			break
		file_size+=len(buffer)
		f.write(buffer)
		signal.emit(file_size)
	f.close()
	form.newmsgq.put("Скачали "+str(prettier_size(file_size)))

def updatemsg():
	global msgnumber,msgid_answer,msglist,echo

	echocount=len(msglist)

	if echocount == 0: # если мы в пустой эхе, кнопки нам не нужны
		return

	msgid_answer=msglist[msgnumber]
	msg=getMsgEscape(msgid_answer)

	repto=msg.get("repto") or "-"

	if (repto!="-"):
		repto="<a href='#ii:"+repto+"'>"+repto+"</a>"

	msgtext="msgid: "+msgid_answer+"<br />"+"Ответ на: "+repto+"<br />"+formatDate(msg.get('time'))+"<br />"+msg.get('subj')+"<br /><b>"+msg.get('sender')+" ("+msg.get('addr')+")  ->  "+msg.get('to')+"</b><br />"

	form.listWidget.setCurrentRow(msgnumber)
	form.textBrowser.setHtml(msgtext+"<br />"+reparseMessage(msg.get('msg')))
	form.label.setText( echo + "  |  " + str(echocount - msgnumber) + " из " + str(echocount))

	if config["rememberEchoPosition"] and form.echoPosition != None:
		form.echoPosition[echo]=echocount-msgnumber

	if msgid_answer in form.favorites_array["list"]:
		form.checkBox.setChecked(True)
	else:
		form.checkBox.setChecked(False)

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
	global echo, curr_outbox_id
	writemsg.writeNew(echo, curr_outbox_id)

def answer(event):
	global msgid_answer, curr_outbox_id
	writemsg.answer(msgid_answer, curr_outbox_id)

def sendWrote_operation():
	countsent=0

	def errorCb(tossfile, error):
		form.errorsq.put(["Ошибка ноды при отправке "+tossfile+": ", error])

	try:
		countsent=sender.sendMessages(getproxy(), errorCb)
	except stoppedDownloadException as e:
		form.newmsgq.put(e)
	except Exception as e:
		form.newmsgq.put(e)
		form.errorsq.put(["Ошибка отправки: ", e])
	form.newmsgq.put(countsent)

def sendWrote(event):
	result=form.processNewThread(sendWrote_operation)

	if (not isinstance(result, Exception)):
		mbox("Отправлено сообщений: "+str(result))

def setUIResize(filename, object):
	# подгрузка интерфейса с учётом предыдущего размера окна
	currentsize=object.size()
	uic.loadUi(filename,object)
	object.resize(currentsize) # восстанавливаем предыдущий размер

def mbox(text):
	form.mbox.setText(text)
	form.mbox.exec_()

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
	string=commenttemplate.sub("\g<1><font color='brown'>\g<3>\g<4></font>", string)
	string=ii_link.sub("<a href='#ii:\g<1>'>\g<0></a>", string)

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
	global curr_outbox_id
	link=link.toString()

	if (link.startswith("#")): # если перед нами ii-ссылка
		link=link[1:] # срезаем первые ненужные символы
		data=link.split(":")

		if not len(data) > 1:
			print(data)
			return
		word=data[0]
		link=data[1]

		if word == "ii":
			if "." in link:
				curr_outbox_id = outbox_id_by_echoarea(link)
				form.viewwindow(link, curr_outbox_id) # идём в эху
			else:
				form.openMessageView(link) # смотрим сообщение
		elif word == "answer": # отвечаем на msgid
			if not curr_outbox_id:
				target_outbox_id = outbox_id_by_echoarea(getMsg(link).get("echo"))

				if target_outbox_id is not None:
					writemsg.answer(link, target_outbox_id)
				else:
					curr_outbox_id = config["servers"][0]["outbox_storage_id"]
					writemsg.answer(link, curr_outbox_id)
					curr_outbox_id = None
			else:
				writemsg.answer(link, curr_outbox_id)

	else:
		print("opening link in default browser")
		webbrowser.open(link)

class Form(QtWidgets.QMainWindow):
	updateSignal=QtCore.pyqtSignal(str, name="update_signal")
	dl_label_signal=QtCore.pyqtSignal(int, name="dl_label_signal")

	def __init__(self):
		global msglist,msgnumber,listlen
		super(Form, self).__init__()

		windowIcon = QtGui.QIcon('artwork/cutiefeed.svg')
		stylesheet = read_file('qtgui-files/style.qss')
		self.setStyleSheet(stylesheet)

		self.newmsgq=queue.Queue()
		self.errorsq=queue.Queue()
		self.loadviewq=queue.Queue()

		self.networkingThread=Thread()
		self.loadViewThread=Thread()
		self.updateTB=Thread()

		self.setWindowIcon(windowIcon)
		self.mbox=QtWidgets.QMessageBox()
		self.mbox.setText("")
		self.boldFont=QtGui.QFont()
		self.boldFont.setBold(True)
		self.favoritesChanged=False

		# настраиваем диалог удаления тоссов

		self.clearMessages=QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, "Подтверждение", "Удалить исходящие сообщения?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
		self.deleteAll=QtWidgets.QCheckBox("В том числе отправленные")
		self.clearMessages.setCheckBox(self.deleteAll)

		self.clearXC=QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, "Подтверждение", "Удалить данные /x/c?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
		self.clearCache=QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, "Подтверждение", "Удалить кэш для эх?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
		self.echoPosition=None

		self.setupClientConfig()
		self.setupServersConfig()
		self.setupUnsentView()
		self.setupAdditional()
		self.setupFavorites()
		self.setupMenu()
		self.setupHelp()

		# если запускаем клиент в первый раз, сначала показываются настройки
		if (config["firstrun"]==True):
			config["firstrun"]=False
			global form
			form=self # костыль, иначе запрос списка эх не заработает
			self.execServersConfig()
			if not config["autoSaveChanges"]:
				self.saveChanges()

		try:
			f=open(paths.sessioncache)
			self.sessionCache=json.load(f)
			f.close()
			self.currentStation = self.sessionCache["currentStation"]
		except:
			self.sessionCache={}
			self.currentStation = 0

		self.mainwindow()

		if config["maximized"]:
			self.setWindowState(QtCore.Qt.WindowMaximized)
		else:
			self.resize(580, 452)

	def mainwindow(self):
		setUIResize("qtgui-files/mainwindow.ui",self)

		global echo, msgid_answer # для правильной работы открытия ii-ссылок в окне просмотра исходящих
		echo="none"
		msgid_answer="none"

		self.pushButton.clicked.connect(self.getNewText)
		self.pushButton_2.clicked.connect(sendWrote)
		self.pushButton_3.clicked.connect(self.displayOfflineEchos)
		self.pushButton_4.clicked.connect(self.updateMainView)
		self.menuButton.setMenu(self.clMenu)

		for server in servers:
			self.comboBox.addItem(server["adress"])

		if self.currentStation >= len(servers):
			self.currentStation = 0

		self.comboBox.setCurrentIndex(self.currentStation)
		self.listWidget.addItems(servers[self.currentStation]["echoareas"])

		self.comboBox.currentIndexChanged.connect(self.loadEchoList)
		self.listWidget.itemActivated.connect(self.openViewWindow)

	def viewwindow(self, echoarea, outbox_id):
		global msglist,msgnumber,listlen,echo,curr_outbox_id
		echo=echoarea
		curr_outbox_id=outbox_id

		setUIResize("qtgui-files/viewwindow.ui",self)

		self.setWindowTitle("Просмотр сообщений: "+echoarea)

		msglist=getMsgList(echo)
		listlen=len(msglist)

		if config["rememberEchoPosition"]:
			if self.echoPosition == None:
				self.echoPosition=get_pos_cache()
			msgnumber=get_position(echo, self.echoPosition)

			if msgnumber == None or msgnumber >= listlen:
				msgnumber = 0
			else:
				msgnumber = listlen - msgnumber
		else:
			msgnumber = 0

		self.processProgressBar(self.loadEchoBase)
		msglist.reverse()

		self.listWidget.currentRowChanged.connect(lbselect)
		self.listWidget.setCurrentRow(msgnumber)

		self.pushButton.clicked.connect(self.mainwindow)
		self.pushButton_2.clicked.connect(msgminus)
		self.pushButton_3.clicked.connect(msgplus)
		self.pushButton_4.clicked.connect(sendWrote)
		self.pushButton_5.clicked.connect(answer)
		self.pushButton_6.clicked.connect(c_writeNew)
		self.pushButton_7.clicked.connect(self.getNewText)
		self.checkBox.clicked.connect(self.favorites_toggle)

		self.menuButton.setMenu(self.clMenu)
		self.textBrowser.anchorClicked.connect(openLink)

	def getDialog(self):
		setUIResize("qtgui-files/getwindow.ui",self)

		self.pushButton.clicked.connect(self.getNewText)
		self.pushButton_2.clicked.connect(self.mainwindow)
		self.newMsgTextBrowser.setParent(self)
		self.verticalLayout.addWidget(self.newMsgTextBrowser)

		global curr_outbox_id
		curr_outbox_id = None # для открытия ii-ссылок для ответа на сообщения

	def processNewThread(self, function, args=[], takeResult=True):
		if self.networkingThread.isAlive():
			return

		debugform.appear()

		self.networkingThread=Thread(target=function, args=args)
		self.networkingThread.daemon=True
		self.networkingThread.start()

		while (self.networkingThread.isAlive()):
			if (not gprintq.empty()):
				debugform.addText(gprintq.get())
			app.processEvents()

		while (not self.errorsq.empty()):
			error=self.errorsq.get()
			mbox(error[0]+'\n\n'+str(error[1]))

		self.networkingThread.join()

		debugform.disappear()

		if takeResult:
			return self.newmsgq.get()

	def loadEchoBase(self):
		global msglist, listlen
		with self.loadviewq.mutex:
			self.loadviewq.queue.clear()

		subjes=get_subj_cache(echo)

		if len(subjes) != listlen:
			cache=open(os.path.join(paths.subjcachedir, echo), "w")
			for i in range(listlen):
				subj=getMsg(msglist[i]).get('subj')
				self.loadviewq.put_nowait([i,subj])
				cache.write(subj+"\n")
			cache.close()
		else:
			for i in range(listlen):
				self.loadviewq.put_nowait([i,subjes[i]])

	def processProgressBar(self, function):
		self.setVisible(0)

		self.progress=QtWidgets.QProgressDialog(self)
		self.progress.setLabel(QtWidgets.QLabel("Подгружаем эху..."))
		self.progress.setAutoClose(True)

		self.progress.setMaximum(listlen-1)
		self.progress.show()

		self.loadViewThread=Thread(target=function)
		self.loadViewThread.daemon=True
		self.loadViewThread.start()

		while True:
			app.processEvents()

			queueFull=(not self.loadviewq.empty())
			threadAlive=self.loadViewThread.isAlive()
			if (queueFull or threadAlive):
				if (queueFull):
					element=self.loadviewq.get(timeout=5)
					self.listWidget.insertItem(0, element[1]) # это сабж вообще-то
					self.progress.setValue(element[0]) # а это - значение прогрессбара
			else:
				break

		self.loadViewThread.join()
		self.setVisible(1)
		self.progress.hide()
		self.progress.destroy()

	def getNewMessages(self):
		def fx(msgids):
			if len(msgids) > 0:
				self.newmsgq.put(msgids)

		proxy_config=getproxy()
		for server in servers:
			if not server["fetch_enabled"]:
				print("skip fetching " + server["adress"])
				continue
			try:
				if (server["advancedue"] == False):
					uelimit=False
				else:
					uelimit=server["uelimit"]
					# uelimit - сколько msgid скачивать максимум при наличии расширенной схемы
					# если стоит в False, то скачиваем все

				msgidsNew=webfetch.fetch_messages(server["adress"], server["echoareas"], server["xcenable"], fetch_limit=uelimit, one_request_limit=config["oneRequestLimit"], proxy=proxy_config, pervasive_ue=server["pervasiveue"], callback=fx, cut_remote_index=server["cut_remote_index"], connTimeout=config["connectionTimeout"])
			except stoppedDownloadException:
				break
			except Exception as e:
				self.errorsq.put([server["adress"]+": ошибка получения сообщений (проблемы с интернетом?)", e])

	def getNewText(self):
		self.newMsgTextBrowser=QtWidgets.QTextBrowser(None)
		self.newMsgTextBrowser.anchorClicked.connect(openLink)
		self.newMsgTextBrowser.setOpenLinks(False)

		self.updateSignal.connect(self.newMsgTextBrowser.append, QtCore.Qt.QueuedConnection)

		self.gotMsgs=False
		self.windowFlag=False
		def updateTextBrowser(signal):
			while True:
				if not self.newmsgq.empty():
					if not self.gotMsgs:
						self.newMsgTextBrowser.insertHtml("Новые сообщения:")
						self.gotMsgs=True
					msgids=self.newmsgq.get()
					htmlcode=""
					for msgid in msgids:
						arr=getMsgEscape(msgid)
						msgid=arr.get('id')
						echo=arr.get('echo')
						subj=arr.get('subj')

						if cache_exists(echo):
							append_subj_cache(subj, echo)

						htmlcode+="<hr /><br /><a href='#ii:"+echo+"'>"+echo+"</a><br />msgid: <a href='#answer:"+msgid+"'>"+msgid+"</a><br />"+formatDate(arr.get('time'))+"<br />"+subj+"<br /><b>"+arr.get('sender')+' ('+arr.get('addr')+') -> '+arr.get('to')+"</b><br /><br />"+reparseMessage(arr.get('msg'))
					signal.emit(htmlcode)
				else:
					if not self.networkingThread.isAlive():
						return

		if self.networkingThread.isAlive() or self.updateTB.isAlive():
			return

		debugform.appear()

		self.networkingThread=Thread(target=self.getNewMessages)
		self.networkingThread.daemon=True
		self.networkingThread.start()

		self.updateTB=Thread(target=updateTextBrowser, args=[self.updateSignal])
		self.updateTB.daemon=True
		self.updateTB.start()

		while (self.networkingThread.isAlive()):
			if self.gotMsgs and not self.windowFlag:
				self.getDialog()
				self.windowFlag=True
			if (not gprintq.empty()):
				debugform.addText(gprintq.get())
			app.processEvents()

		while (not self.errorsq.empty()):
			error=self.errorsq.get()
			mbox(error[0]+'\n\n'+str(error[1]))

		self.networkingThread.join()
		self.updateTB.join()

		debugform.disappear()

		if not self.gotMsgs:
			self.newMsgTextBrowser.destroy()
			mbox('Новых сообщений нет.')
		else:
			global curr_outbox_id
			curr_outbox_id = None

	def deleteTosses(self):
		answer=self.clearMessages.exec_()
		counter=0

		if answer == QtWidgets.QMessageBox.Yes:
			for server in config["servers"]:
				outbox_id = server["outbox_storage_id"]
				path = os.path.join(paths.tossesdir, outbox_id)

				for filename in os.listdir(path):
					if self.deleteAll.isChecked() or filename[-5:] == ".toss":
						counter+=1
						delete(os.path.join(path, filename))

			if counter>0:
				mbox("Удалено сообщений: "+str(counter))
			else:
				mbox("Удалять нечего")

	def deleteXC(self):
		answer=self.clearXC.exec_()
		counter=0

		if answer == QtWidgets.QMessageBox.Yes:
			for filename in os.listdir(paths.datadir):
				if filename[:5]=="base-":
					counter+=1
					delete(os.path.join(paths.datadir, filename))

			if counter>0:
				mbox("Удалено файлов: "+str(counter))
			else:
				mbox("Удалять нечего")

	def deleteCache(self):
		answer=self.clearCache.exec_()
		counter=0

		if answer == QtWidgets.QMessageBox.Yes:
			if os.path.exists(paths.echopositionfile):
				delete(paths.echopositionfile)
				counter+=1

			if os.path.exists(paths.sessioncache):
				delete(paths.sessioncache)
				counter+=1

			if self.echoPosition != None:
				self.echoPosition=None

			self.currentStation = 0

			for filename in os.listdir(paths.subjcachedir):
				delete(os.path.join(paths.subjcachedir, filename))
				counter+=1

			if counter>0:
				mbox("Удалено файлов: "+str(counter))
			else:
				mbox("Удалять нечего")

	def deleteOneEcho(self):
		echoarea=self.additional.comboBox_2.currentText()

		question=QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, "Подтверждение", "Удалить эху "+echoarea+"?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

		answer=question.exec_()
		question.destroy()

		if (answer == QtWidgets.QMessageBox.Yes):
			global echo
			if echo == echoarea:
				self.mainwindow()

			def function():
				msglist=getMsgList(echoarea)
				for msgid in msglist:
					delete(os.path.join(paths.msgdir, msgid))
				delete(os.path.join(paths.indexdir, echoarea))
				delete(os.path.join(paths.subjcachedir, echoarea))
			self.processNewThread(function, takeResult=False)
			self.additional_update_echoes()

	def deleteAllEchoes(self):
		countItems=self.additional.comboBox_2.count()

		echoes=[]
		for i in range(countItems):
			echoes.append(self.additional.comboBox_2.itemText(i))

		question=QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, "Подтверждение", "Удалить ВСЮ БАЗУ ДАННЫХ?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

		answer=question.exec_()
		question.destroy()

		if (answer == QtWidgets.QMessageBox.Yes):
			self.mainwindow()

			def function():
				for echo in echoes:
					msglist=getMsgList(echo)
					for msgid in msglist:
						delete(os.path.join(paths.msgdir, msgid))
					delete(os.path.join(paths.indexdir, echo))
					delete(os.path.join(paths.subjcachedir, echo))
			self.processNewThread(function, takeResult=False)
			self.additional_update_echoes()

	def setupMenu(self):
		self.clMenu=QtWidgets.QMenu()

		clientSettingsAction=QtWidgets.QAction("Настройки клиента", self)
		serversSettingsAction=QtWidgets.QAction("Настройки станций", self)
		saveSettingsAction=QtWidgets.QAction("Сохранить настройки", self)
		additionalFeaturesAction=QtWidgets.QAction("Дополнительные фичи", self)
		deleteTossesAction=QtWidgets.QAction("Удалить исходящие", self)
		deleteXCAction=QtWidgets.QAction("Удалить данные /x/c", self)
		deleteCacheAction=QtWidgets.QAction("Удалить кэш", self)
		helpAction=QtWidgets.QAction("Справка", self)
		unsentViewAction=QtWidgets.QAction("Просмотр исходящих", self)
		favoritesAction=QtWidgets.QAction("Избранные сообщения", self)

		clientSettingsAction.triggered.connect(self.execClientConfig)
		serversSettingsAction.triggered.connect(self.execServersConfig)
		saveSettingsAction.triggered.connect(self.saveChanges)
		additionalFeaturesAction.triggered.connect(self.execAdditional)
		deleteTossesAction.triggered.connect(self.deleteTosses)
		deleteXCAction.triggered.connect(self.deleteXC)
		deleteCacheAction.triggered.connect(self.deleteCache)
		helpAction.triggered.connect(self.showHelp)
		unsentViewAction.triggered.connect(self.execUnsentView)
		favoritesAction.triggered.connect(self.execFavorites)

		self.clMenu.addAction(unsentViewAction)
		self.clMenu.addAction(favoritesAction)
		self.clMenu.addSeparator()

		self.clMenu.addAction(clientSettingsAction)
		self.clMenu.addAction(serversSettingsAction)
		self.clMenu.addAction(saveSettingsAction)
		self.clMenu.addAction(additionalFeaturesAction)

		self.clMenu.addSeparator()
		self.clMenu.addAction(deleteTossesAction)
		self.clMenu.addAction(deleteXCAction)
		self.clMenu.addAction(deleteCacheAction)

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
		self.serversConfig.pushButton_5.clicked.connect(self.load_list_txt) # получение списка эх с ноды
		self.serversConfig.pushButton_6.clicked.connect(self.x_features_autoConfig) # автонастройка

		self.serversConfig.addTabButton.clicked.connect(self.tabAddRequest)
		self.serversConfig.deleteTabButton.clicked.connect(self.tabDeleteRequest)
		self.serversConfig.accepted.connect(self.applyServersConfigFromButton)

	def setupUnsentView(self):
		def updateView(item):
			if item == None: # например, если мы удалили последнее
				self.unsentView.textBrowser.clear()
				return

			filename = item.data(QtCore.Qt.UserRole)
			s=getOutMsgEscape(filename)
			repto=s.get("repto") or "-"

			if (repto!="-"):
				repto="<a href='#ii:"+repto+"'>"+repto+"</a>"

			output="Ответ на: "+repto+"<br />"+s.get("echo")+"<br />"+s.get("subj")+"<br /><b>"+s.get("to")+"</b><br /><br />"+reparseMessage(s.get("msg"))
			self.unsentView.textBrowser.setHtml(output)

		def left():
			msgnumber=self.unsentView.listWidget.currentRow()
			if(msgnumber>0):
				msgnumber-=1;
				self.unsentView.listWidget.setCurrentRow(msgnumber)

		def right():
			msgnumber=self.unsentView.listWidget.currentRow()
			listlen=self.unsentView.listWidget.count()
			if(msgnumber<(listlen-1)):
				msgnumber+=1;
				self.unsentView.listWidget.setCurrentRow(msgnumber)

		def edit():
			item=self.unsentView.listWidget.currentItem()
			if item != None:
				filename=item.data(QtCore.Qt.UserRole)
				writemsg.openEditor(filename)

		def deleteFile():
			msgnumber=self.unsentView.listWidget.currentRow()
			item=self.unsentView.listWidget.takeItem(msgnumber)
			if item != None:
				filename=item.data(QtCore.Qt.UserRole)
				delete(filename)

		def delTosses():
			self.deleteTosses()
			self.loadUnsentView()

		self.unsentView=uic.loadUi("qtgui-files/unsent.ui")
		self.unsentView.pushButton.clicked.connect(delTosses)
		self.unsentView.pushButton_2.clicked.connect(left)
		self.unsentView.pushButton_3.clicked.connect(right)
		self.unsentView.pushButton_4.clicked.connect(sendWrote)
		self.unsentView.pushButton_5.clicked.connect(deleteFile)
		self.unsentView.pushButton_6.clicked.connect(edit)
		self.unsentView.pushButton_7.clicked.connect(self.loadUnsentView)
		self.unsentView.textBrowser.anchorClicked.connect(openLink)
		self.unsentView.listWidget.currentItemChanged.connect(updateView)

	def setupAdditional(self):
		self.additional=uic.loadUi("qtgui-files/additional.ui")
		self.additional.filename=""

		self.additional.pushButton.clicked.connect(self.download_blacklist_txt)
		self.additional.pushButton_2.clicked.connect(self.choose_blacklist_file)
		self.additional.pushButton_3.clicked.connect(self.blacklist_cleanup)
		self.additional.pushButton_4.clicked.connect(self.try_load_xfilelist)
		self.additional.pushButton_5.clicked.connect(self.deleteAllEchoes)
		self.additional.pushButton_6.clicked.connect(self.deleteOneEcho)
		self.additional.pushButton_7.clicked.connect(self.copy_blacklist_txt)
		self.dl_label_signal.connect(self.dl_set_label, QtCore.Qt.QueuedConnection)
		self.additional.tableView.doubleClicked.connect(self.try_load_file)
		self.additional.tableView.horizontalHeader().setStretchLastSection(True)

	def setupFavorites(self):
		def updateView(item):
			if item == None:
				self.favorites.textBrowser.clear()
				return

			msgid = item.data(QtCore.Qt.UserRole)
			msg=getMsgEscape(msgid)
			echo=msg.get("echo")
			repto=msg.get("repto") or "-"

			if repto!="-":
				repto="<a href='#ii:"+repto+"'>"+repto+"</a>"

			msgtext="<a href='#ii:"+echo+"'>"+echo+"</a><br />msgid: <a href='#answer:"+msgid+"'>"+msgid+"</a><br />"+"Ответ на: "+repto+"<br />"+formatDate(msg.get('time'))+"<br />"+msg.get('subj')+"<br /><b>"+msg.get('sender')+" ("+msg.get('addr')+")  ->  "+msg.get('to')+"</b><br />"

			self.favorites.textBrowser.setHtml(msgtext+"<br />"+reparseMessage(msg.get('msg')))

		def left():
			msgnumber=self.favorites.listWidget.currentRow()
			if(msgnumber>0):
				msgnumber-=1;
				self.favorites.listWidget.setCurrentRow(msgnumber)

		def right():
			msgnumber=self.favorites.listWidget.currentRow()
			listlen=self.favorites.listWidget.count()
			if(msgnumber<(listlen-1)):
				msgnumber+=1;
				self.favorites.listWidget.setCurrentRow(msgnumber)

		def deleteFavorite():
			self.favoritesChanged=True
			msgnumber=self.favorites.listWidget.currentRow()
			item=self.favorites.listWidget.takeItem(msgnumber)
			if item != None:
				msgid=item.data(QtCore.Qt.UserRole)
				self.favorites_array["list"].remove(msgid)
				del self.favorites_array["subjes"][msgid]

		self.favorites=uic.loadUi("qtgui-files/favorites.ui")
		self.favorites.pushButton_2.clicked.connect(left)
		self.favorites.pushButton_3.clicked.connect(right)
		self.favorites.pushButton_5.clicked.connect(deleteFavorite)
		self.favorites.listWidget.currentItemChanged.connect(updateView)
		self.favorites.textBrowser.anchorClicked.connect(openLink)
		self.favorites_array = get_favorites()

	def loadInfo_client(self):
		self.clientConfig.lineEdit.setText(config["editor"])
		self.clientConfig.lineEdit_2.setText(config["proxy"])
		self.clientConfig.lineEdit_3.setText(config["proxyType"])
		self.clientConfig.listWidget.clear()
		self.clientConfig.listWidget.addItems(config["offline-echoareas"])

		if (len(config["offline-echoareas"])>0):
			self.clientConfig.listWidget.setCurrentRow(0)

		self.clientConfig.checkBox.setChecked(config["defaultEditor"])
		self.clientConfig.checkBox_2.setChecked(config["firstrun"])
		self.clientConfig.checkBox_3.setChecked(config["autoSaveChanges"])
		self.clientConfig.checkBox_4.setChecked(config["useProxy"])
		self.clientConfig.checkBox_5.setChecked(config["rememberEchoPosition"])
		self.clientConfig.checkBox_6.setChecked(config["maximized"])

		self.clientConfig.spinBox.setValue(config["oneRequestLimit"])
		self.clientConfig.spinBox_2.setValue(config["connectionTimeout"])

	def loadInfo_servers(self, index=0):
		curr=servers[index]

		self.serversConfig.lineEdit.setText(curr["adress"])
		self.serversConfig.lineEdit_2.setText(curr["authstr"])
		self.serversConfig.listWidget.clear()
		self.serversConfig.listWidget.addItems(curr["echoareas"])

		if (len(curr["echoareas"])>0):
			self.serversConfig.listWidget.setCurrentRow(0)

		self.serversConfig.checkBox.setChecked(curr["xcenable"])
		self.serversConfig.checkBox_2.setChecked(curr["advancedue"])
		self.serversConfig.checkBox_3.setChecked(curr["pervasiveue"])
		self.serversConfig.checkBox_4.setChecked(curr["fetch_enabled"])
		self.serversConfig.spinBox.setValue(curr["uelimit"])
		self.serversConfig.spinBox_2.setValue(curr["cut_remote_index"])

		is_ue_enabled=curr["advancedue"]
		self.serversConfig.checkBox_3.setEnabled(is_ue_enabled)
		self.serversConfig.spinBox.setEnabled(is_ue_enabled)

	def loadInfo_additional(self):
		self.additional.comboBox.clear()
		self.additional.comboBox_3.clear()

		for server in servers:
			self.additional.comboBox.addItem(server["adress"])
			self.additional.comboBox_3.addItem(server["adress"])

		self.additional_update_echoes()

	def loadInfo_favorites(self):
		self.favorites.listWidget.clear()
		messages = self.favorites_array["list"]
		for msgid in reversed(messages):
			list_item=QtWidgets.QListWidgetItem(self.favorites.listWidget)
			list_item.setText(self.favorites_array["subjes"][msgid])
			list_item.setData(QtCore.Qt.UserRole, msgid)

			self.favorites.listWidget.insertItem(0, list_item)

	def loadEchoList(self, index=0):
		self.currentStation = index
		self.listWidget.clear()
		self.listWidget.addItems(servers[index]["echoareas"])

	def loadUnsentView(self):
		def loader(self):
			try:
				print("get file list")
				files=getOutList(config["servers"])
				for msg in files:
					self.newmsgq.put(msg)
			except Exception as e:
				self.newmsgq.put(e)
				self.errorsq.put(["Ошибка: ", e])
				return

		self.processNewThread(loader, args=[self], takeResult=False)

		self.unsentView.listWidget.clear()
		while True:
			queueFull=(not self.newmsgq.empty())
			threadAlive=self.networkingThread.isAlive()
			if (queueFull or threadAlive):
				if (queueFull):
					element=self.newmsgq.get(timeout=5)
					list_item=QtWidgets.QListWidgetItem(self.unsentView.listWidget)
					list_item.setText(element[-20:])
					list_item.setToolTip(element)
					list_item.setData(QtCore.Qt.UserRole, element)
					if element[-5:] == ".toss":
						list_item.setFont(self.boldFont)

					self.unsentView.listWidget.insertItem(0, list_item)
			else:
				break
		if self.unsentView.listWidget.count() == 0:
			return False
		self.unsentView.listWidget.setCurrentRow(0)
		return True

	def updateMainView(self):
		index=self.comboBox.currentIndex()

		self.comboBox.clear()
		for server in servers:
			self.comboBox.addItem(server["adress"])

		self.comboBox.setCurrentIndex(index)

	def favorites_toggle(self, state):
		global msgid_answer
		self.favoritesChanged = True
		checked = self.checkBox.isChecked()

		if not checked:
			if msgid_answer not in self.favorites_array["list"]:
				return
			del self.favorites_array["subjes"][msgid_answer]
			self.favorites_array["list"].remove(msgid_answer)
		else:
			item = self.listWidget.currentItem()
			if item == None:
				return
			self.favorites_array["subjes"][msgid_answer]=item.text()
			self.favorites_array["list"].append(msgid_answer)

	def additional_update_echoes(self):
		self.additional.comboBox_2.clear()

		echolist=os.listdir(paths.indexdir)
		self.additional.comboBox_2.addItems(echolist)

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

	def execUnsentView(self):
		loaded=self.loadUnsentView()
		if loaded:
			self.unsentView.exec_()
		else:
			mbox("Исходящих нет")

	def execAdditional(self):
		self.loadInfo_additional()
		self.additional.exec_()

	def execFavorites(self):
		self.loadInfo_favorites()
		self.favorites.listWidget.setCurrentRow(0)
		self.favorites.exec_()

	def applyClientConfig(self):
		config["editor"]=self.clientConfig.lineEdit.text()
		config["proxy"]=self.clientConfig.lineEdit_2.text()
		config["proxyType"]=self.clientConfig.lineEdit_3.text()
		config["defaultEditor"]=self.clientConfig.checkBox.isChecked()
		config["firstrun"]=self.clientConfig.checkBox_2.isChecked()
		config["autoSaveChanges"]=self.clientConfig.checkBox_3.isChecked()
		config["useProxy"]=self.clientConfig.checkBox_4.isChecked()
		config["rememberEchoPosition"]=self.clientConfig.checkBox_5.isChecked()
		config["maximized"]=self.clientConfig.checkBox_6.isChecked()
		config["oneRequestLimit"]=self.clientConfig.spinBox.value()
		config["connectionTimeout"]=self.clientConfig.spinBox_2.value()

		config["offline-echoareas"]=[]

		count=self.clientConfig.listWidget.count()
		for index in range(0,count):
			config["offline-echoareas"].append(self.clientConfig.listWidget.item(index).text())

		self.saveOrNot()

	def applyServersConfig(self, index=0):
		servers[index]["adress"]=self.serversConfig.lineEdit.text()
		servers[index]["authstr"]=self.serversConfig.lineEdit_2.text()
		servers[index]["xcenable"]=self.serversConfig.checkBox.isChecked()
		servers[index]["advancedue"]=self.serversConfig.checkBox_2.isChecked()
		servers[index]["pervasiveue"]=self.serversConfig.checkBox_3.isChecked()
		servers[index]["fetch_enabled"]=self.serversConfig.checkBox_4.isChecked()
		servers[index]["uelimit"]=self.serversConfig.spinBox.value()
		servers[index]["cut_remote_index"]=self.serversConfig.spinBox_2.value()

		servers[index]["echoareas"]=[]
		count=self.serversConfig.listWidget.count()

		for itemNumber in range(0,count):
			servers[index]["echoareas"].append(self.serversConfig.listWidget.item(itemNumber).text())

		config["servers"]=servers

		self.saveOrNot()

	def load_list_txt(self):
		rawlist=load_raw_file(self.serversConfig.lineEdit.text()+"list.txt")
		echoes=[x.split(":") for x in rawlist.splitlines()]
		list_dialog=uic.loadUi("qtgui-files/list.txt.ui")

		model=QtGui.QStandardItemModel(len(echoes), 3)
		list_dialog.tableView.setModel(model)
		list_dialog.tableView.horizontalHeader().setStretchLastSection(True)

		for row in range(len(echoes)):
			for col in range(3):
				index=model.index(row, col)
				model.setData(index, echoes[row][col])

		list_dialog.tableView.resizeRowsToContents()
		list_dialog.tableView.resizeColumnsToContents()

		answer=list_dialog.exec_()
		if answer == 1:
			self.serversConfig.listWidget.clear()
			echoes=[x[0] for x in echoes]
			self.serversConfig.listWidget.addItems(echoes)

		list_dialog.destroy()

	def download_blacklist_txt(self):
		server=self.additional.comboBox_3.currentText()
		raw_blacklist=load_raw_file(server+"blacklist.txt")
		if (raw_blacklist != None and raw_blacklist != ""):
			f=open(paths.blacklistfile, "w")
			f.write(raw_blacklist)
			f.close()
			blacklist_func.blacklist=blacklist_func.getBlackList()
			mbox("Чёрный список загружен")
		else:
			mbox("Ошибка загрузки")

	def choose_blacklist_file(self):
		filename=QtWidgets.QFileDialog.getOpenFileName(self.additional, "Выбрать файл ЧС", paths.homedir, filter="Текстовые файлы (*.txt)")[0]
		self.additional.filename=filename

	def copy_blacklist_txt(self):
		if self.additional.filename == "":
			mbox("Файл не выбран!")
		else:
			print("Выбрали "+self.additional.filename)
			shutil.copy(self.additional.filename, paths.blacklistfile)
			blacklist_func.blacklist=blacklist_func.getBlackList()
			mbox("ЧС скопирован, можно чистить")

	def blacklist_cleanup(self):
		def worker():
			echolist=os.listdir(paths.indexdir)
			blacklist_func.blacklistCleanup(echolist)

		self.processNewThread(worker, takeResult=False)

	def try_load_xfilelist(self):
		index=self.additional.comboBox.currentIndex()
		server=servers[index]

		data = urllib.parse.urlencode({'pauth': server["authstr"]}).encode('utf8')

		result=load_raw_file(server["adress"] + 'x/filelist', data)
		if result == "" or result == None:
			mbox("Что-то здесь не то (сервер не поддерживает /x/file или проблемы с интернетом)")
		else:
			filearr=[]

			files=result.splitlines()
			for file in files:
				a=file.split(":")

				if (len(a)<3):
					mbox(file)
					return
				else:
					filearr.append([a[0], prettier_size(int(a[1])), a[2]])
			model=QtGui.QStandardItemModel(len(filearr), 3)
			self.additional.tableView.setModel(model)

			for row in range(len(filearr)):
				for col in range(3):
					index=model.index(row, col)
					model.setData(index, filearr[row][col])

			self.additional.tableView.resizeRowsToContents()
			self.additional.tableView.resizeColumnsToContents()

	def try_load_file(self, index):
		i=self.additional.comboBox.currentIndex()
		server=servers[i]

		model=index.model()
		row=index.row()
		filename=model.index(row, 0).data()
		expectSize=model.index(row, 1).data()

		savename=QtWidgets.QFileDialog.getSaveFileName(self.additional, "Куда сохраняем", paths.homedir+"/"+filename)[0]
		if savename=="":
			return

		# теперь как-то пробуем скачать файл

		self.additional.label_7.setText("")
		self.additional.count=0
		self.additional.total=" из "+expectSize;

		timer=QtCore.QTimer(self.additional)
		timer.timeout.connect(self.dl_update_label)
		timer.start(1000)
		result=self.processNewThread(xfile_download, args=[server, filename, savename, self.dl_label_signal])
		mbox(result)
		timer.stop()

	def dl_set_label(self, size):
		self.additional.count=size

	def dl_update_label(self):
		text=prettier_size(self.additional.count)+self.additional.total
		self.additional.label_7.setText(text)
		print(text)

	def x_features_autoConfig(self):
		nodeAdress=self.serversConfig.lineEdit.text()

		if not nodeAdress.endswith("/"):
			# Беспечный пользователь забыл слэш в конце адреса ноды
			# Проставляем за него
			mbox("В конце адреса станции должен стоять слэш \"/\". Запомни это на будущее.")
			nodeAdress+="/"
			self.serversConfig.lineEdit.setText(nodeAdress)

		raw_data=load_raw_file(nodeAdress+"x/features")
		if raw_data is None or raw_data is "":
			mbox("Станция не поддерживает автонастройку, либо проблемы с интернетом. Ставим минимально рабочую конфигурацию.")

		features=raw_data.splitlines()

		self.serversConfig.checkBox.setChecked("x/c" in features)
		self.serversConfig.checkBox_2.setChecked("u/e" in features)

		if "u/e" in features:
			self.serversConfig.checkBox_3.setChecked(False)
			self.serversConfig.spinBox.setValue(defaultServersValues["uelimit"])
			self.serversConfig.spinBox_2.setValue(0)
		else:
			self.serversConfig.spinBox_2.setValue(50)

		if "list.txt" in features:
			self.load_list_txt()

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
			if not config["autoSaveChanges"]: # чтобы не надоедало людям
				mbox("Настройки сохранены")
		else:
			mbox("Упс, сохранить не получилось, смотри в логи.")

	def saveOrNot(self): # смотрим, стоит ли автосохранение настроек
		# если стоит, то сохраняем их
		if config["autoSaveChanges"]:
			self.saveChanges()

	def setupHelp(self):
		helpfile=read_file("readme.html")
		self.helpWindow=uic.loadUi("qtgui-files/readhelp.ui")
		self.helpWindow.textBrowser.setHtml(helpfile)

		pm1=QtGui.QPixmap("artwork/cutiefeed.svg")
		self.helpWindow.label_2.setPixmap(pm1)

		self.helpWindow.textBrowser.anchorClicked.connect(openLink)

	def showHelp(self):
		self.helpWindow.show()

	def tabMovedEvent(self, first, second):
		servers[first], servers[second] = servers[second], servers[first]
		self.oldCurrentTab=self.serversConfig.tabBar.currentIndex()

	def tabAddRequest(self):
		servers.append(defaultServersValues)
		newindex=self.serversConfig.tabBar.addTab(str(len(servers)))
		servers[newindex]["outbox_storage_id"] = uuid.uuid4().hex
		self.serversConfig.tabBar.setCurrentIndex(newindex)

	def tabDeleteRequest(self):
		currindex=self.serversConfig.tabBar.currentIndex()

		path = os.path.join(paths.tossesdir, servers[currindex]["outbox_storage_id"])
		if os.path.exists(path):
			outbox = os.listdir(path)

			if len(outbox) > 0:
				dialog = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, "Подтверждение", "В каталоге "+path+" остались исходящие сообщения ("+str(len(outbox))+"), принадлежащие этой станции. Удалить их тоже?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
				answer = dialog.exec_()

				if answer == QtWidgets.QMessageBox.Yes:
					for file in outbox:
						delete(os.path.join(path, file))
					os.rmdir(path)
				elif answer == QtWidgets.QMessageBox.Cancel:
					return

			else:
				os.rmdir(path)

		self.serversConfig.tabBar.removeTab(currindex)
		del servers[currindex]
		self.loadInfo_servers(self.serversConfig.tabBar.currentIndex())

	def openViewWindow(self, item):
		echoarea = item.text()
		outbox_id = outbox_id_by_address(self.comboBox.currentText())
		self.viewwindow(echoarea, outbox_id)

	def displayOfflineEchos(self):
		self.listWidget.clear()

		if len(config["offline-echoareas"]) > 0:
			self.listWidget.addItems(config["offline-echoareas"])

	def openMessageView(self, msgid):
		global echo, msgid_answer # сохраняем msgid исходной эхи, чтобы
		tmpecho=str(echo) # можно было бы отвечать на сообщения
		tmpmsgid=str(msgid_answer) # после закрытия диалога

		msg=getMsgEscape(msgid)

		repto=msg.get("repto") or "-"

		if (repto!="-"):
			repto="<a href='#ii:"+repto+"'>"+repto+"</a>"

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

	def closeEvent(self, event):
		if config["rememberEchoPosition"] and self.echoPosition != None:
			save_pos_cache(self.echoPosition)

		if self.favoritesChanged:
			save_favorites(self.favorites_array)

		try:
			self.sessionCache["currentStation"]=self.currentStation
			f=open(paths.sessioncache, "w")
			json.dump(self.sessionCache, f)
			f.close()
		except Exception as e:
			print("Ошибка сохранения кэша сессии: "+str(e))

		for obj in [
			self.clientConfig,
			self.serversConfig,
			self.unsentView,
			self.additional,
			self.favorites,
			self.helpWindow,
			self.clearXC,
			self.clearCache,
			self.clearMessages,
			debugform
		]:
			obj.destroy()
		event.accept()

class debugForm(QtWidgets.QDialog):
	def __init__(self):
		super(debugForm, self).__init__()
		setUIResize("qtgui-files/debugview.ui",self)
		self.pushButton.clicked.connect(self.user_stop)

	def user_stop(self):
		ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(form.networkingThread.ident),ctypes.py_object(stoppedDownloadException))

	def addText(sender, text):
		debugform.textBrowser.append(text)

	def appear(self):
		debugform.textBrowser.clear()
		debugform.show()

	def disappear(self):
		gprintq.queue.clear()
		debugform.textBrowser.clear()
		debugform.hide()

	def closeEvent(self, event):
		self.disappear()
		event.ignore()

def my_print(func): # декоратор над стандартным питоновским print'ом
	def wrapper(arg):
		gprintq.put(arg)
		func(arg)
	return wrapper

gprintq=queue.Queue()
print=my_print(print) # теперь print - это уже не print =)
webfetch.print=print
network.print=print
sender.print=print
blacklist_func.print=print
delete=blacklist_func.delete

class stoppedDownloadException(Exception):
	def __init__(self):
		super(stoppedDownloadException, self).__init__("Скачивание остановлено")

app = QtWidgets.QApplication(sys.argv)

debugform=debugForm()
form=Form()

form.show()
sys.exit(app.exec_())
