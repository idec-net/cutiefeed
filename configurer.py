#!/usr/bin/env python2
# -*- coding:utf8 -*-
import locale,sys
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

from getcfg import *
from PyQt5 import QtCore, QtGui, QtWidgets, uic

#def listIncrement(event):
#	currRow=configform.clientConfig.listWidget.currentRow()
#	rowNumbers=configform.clientConfig.listWidget.

def editItem(event):
	lw=event.listWidget()
	event.setFlags(QtCore.Qt.ItemFlags(1|2|32)) # ставим, что элемент активный, что его можно править, и что он выбираемый
	lw.editItem(event)

def deleteItem(event):
	configform.currLw.takeItem(configform.currLw.currentRow())

def addItem(event):
	newListItem=QtWidgets.QListWidgetItem("echoarea.15")
	newListItem.setFlags(QtCore.Qt.ItemFlags(1|2|32))
	targetRow=configform.currLw.currentRow()+1
	configform.currLw.insertItem(targetRow, newListItem)
	configform.currLw.setCurrentRow(targetRow)
	configform.currLw.editItem(newListItem)

def itemUp(event):
	targetRow=configform.currLw.currentRow()-1
	if (targetRow>=0):
		tookItem=configform.currLw.takeItem(targetRow+1)
		configform.currLw.insertItem(targetRow, tookItem)
		configform.currLw.setCurrentRow(targetRow)

def itemDown(event):
	targetRow=configform.currLw.currentRow()+1
	count=configform.currLw.count()
	if (targetRow<count):
		tookItem=configform.currLw.takeItem(targetRow-1)
		configform.currLw.insertItem(targetRow, tookItem)
		configform.currLw.setCurrentRow(targetRow)

class Form(QtWidgets.QWidget):
	def __init__(self):
		super(Form, self).__init__()

		windowIcon=QtGui.QIcon('artwork/iilogo.png')
		self.setWindowIcon(windowIcon)
		self.setWindowTitle('Настройки')

		self.resize(400,500)

		self.setupUI()

		self.setupClientConfig()
		self.setupServersConfig()

		self.clientSettingsButton.clicked.connect(self.execClientConfig)
		self.serversSettingsButton.clicked.connect(self.execServersConfig)
	
	def setupUI(self):
		self.clientSettingsButton=QtWidgets.QPushButton("Настройки клиента")
		self.serversSettingsButton=QtWidgets.QPushButton("Настройки станций и подписок")
		self.saveSettingsButton=QtWidgets.QPushButton("Сохранить изменения")
		self.mbox=QtWidgets.QMessageBox()
		
		self.vertlayout=QtWidgets.QVBoxLayout(self)
		self.setLayout(self.vertlayout)

		self.vertlayout.addWidget(self.clientSettingsButton)
		self.vertlayout.addWidget(self.serversSettingsButton)
		self.vertlayout.addWidget(self.saveSettingsButton)

		self.saveSettingsButton.clicked.connect(self.saveChanges)

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
		self.serversConfig.listWidget.itemDoubleClicked.connect(editItem)
		self.serversConfig.pushButton.clicked.connect(addItem) # кнопка Добавить
		self.serversConfig.pushButton_2.clicked.connect(deleteItem) # кнопка Удалить
		self.serversConfig.pushButton_3.clicked.connect(itemUp) # кнопка Вверх
		self.serversConfig.pushButton_4.clicked.connect(itemDown) # кнопка Вниз

		self.serversConfig.accepted.connect(self.applyServersConfig)
	
	def loadInfo_client(self):
		self.clientConfig.lineEdit.setText(config["editor"])
		self.clientConfig.listWidget.clear()
		self.clientConfig.listWidget.addItems(config["offline-echoareas"])

		if (len(config["offline-echoareas"])>0):
			self.clientConfig.listWidget.setCurrentRow(0)

	def loadInfo_servers(self):
		curr=servers[0]
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
		self.loadInfo_servers()
		self.currLw=self.serversConfig.listWidget
		self.serversConfig.exec_()
	
	def applyClientConfig(self):
		config["editor"]=self.clientConfig.lineEdit.text()
		count=self.clientConfig.listWidget.count()

		config["offline-echoareas"]=[]

		for index in range(0,count):
			config["offline-echoareas"].append(self.clientConfig.listWidget.item(index).text())
	
	def applyServersConfig(self):
		servers[0]["adress"]=self.serversConfig.lineEdit.text()
		servers[0]["authstr"]=self.serversConfig.lineEdit_2.text()
		servers[0]["xtenable"]=self.serversConfig.checkBox.isChecked()

		servers[0]["echoareas"]=[]
		count=self.serversConfig.listWidget.count()
		
		for index in range(0,count):
			servers[0]["echoareas"].append(self.serversConfig.listWidget.item(index).text())

		config["servers"]=servers

	def saveChanges(self):
		result=saveConfig()
		if result:
			self.mbox.setText("Настройки сохранены")
		else:
			self.mbox.setText("Упс, сохранить не получилось, смотри в логи.")
		return self.mbox.exec_()
	
app = QtWidgets.QApplication(sys.argv)
configform=Form()
configform.show()
sys.exit(app.exec_())
