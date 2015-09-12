#!/usr/bin/env python2
# -*- coding:utf8 -*-
import locale,sys
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

from getcfg import *
from PyQt5 import QtCore, QtGui, QtWidgets, uic

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
		
		self.vertlayout=QtWidgets.QVBoxLayout(self)
		self.setLayout(self.vertlayout)

		self.vertlayout.addWidget(self.clientSettingsButton)
		self.vertlayout.addWidget(self.serversSettingsButton)

	def setupClientConfig(self):
		self.clientConfig=uic.loadUi("qtgui-files/clientconfig.ui")

	def setupServersConfig(self):
		self.serversConfig=uic.loadUi("qtgui-files/stations.ui")
	
	def loadInfo_client(self):
		self.clientConfig.lineEdit.setText(config["editor"])
		self.clientConfig.listWidget.clear()
		self.clientConfig.listWidget.addItems(config["offline-echoareas"])

	def loadInfo_servers(self):
		curr=servers[0]
		self.serversConfig.lineEdit.setText(curr["adress"])
		self.serversConfig.lineEdit_2.setText(curr["authstr"])
		self.serversConfig.listWidget.clear()
		self.serversConfig.listWidget.addItems(curr["echoareas"])

		checkState=0

		if curr["xtenable"]==True:
			checkState=2 # ставим, что чекбокс нажат

		self.serversConfig.checkBox.setCheckState(checkState)

	def execClientConfig(self):
		self.loadInfo_client()
		self.clientConfig.exec_()
	
	def execServersConfig(self):
		self.loadInfo_servers()
		self.serversConfig.exec_()
	
app = QtWidgets.QApplication(sys.argv)
form=Form()
form.show()
sys.exit(app.exec_())
