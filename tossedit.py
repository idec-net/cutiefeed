#!/usr/bin/env python3

import sys,os

from PyQt5 import QtCore, QtWidgets, uic

class EditorForm(QtWidgets.QWidget):
	def __init__(self, filename):
		super(EditorForm, self).__init__()
		uic.loadUi("qtgui-files/tosseditor.ui", self)
		
		self.setWindowTitle(filename)
		self.msgobj={"echoarea":"", "to":"All", "subj":"...", "repto":"", "msgtext":""}
		self.mbox=QtWidgets.QMessageBox(self)
		self.filename=filename

		try:
			source=open(self.filename, "rb").read().decode("utf8")
			self.plainTextEdit.setPlainText(source)
			self.tabChanged(0)
		except:
			self.mbox.setText("Не могу открыть файл "+filename)
			self.mbox.exec_()
			self.close()

		self.tabWidget.currentChanged.connect(self.tabChanged)
		self.pushButton.clicked.connect(self.saveFile)
		self.pushButton_2.clicked.connect(self.closeAndDelete)
		self.pushButton_3.clicked.connect(self.closeWithoutSaving)

		self.pushButton.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_S)
		self.plainTextEdit.setFocus()
		self.plainTextEdit_1.setFocus()
	
	def getMsg_From_Source(self):
		source=self.plainTextEdit.toPlainText().splitlines()
		count=len(source)
		
		try:
			self.msgobj["echoarea"]=source[0]
		except:
			self.msgobj["echoarea"]=""
		
		try:
			self.msgobj["to"]=source[1]
		except:
			self.msgobj["to"]=""

		try:
			self.msgobj["subj"]=source[2]
		except:
			self.msgobj["subj"]=""

		try:
			str=source[4]
			if str.startswith("@repto:"):
				self.msgobj["repto"]=str[7:]
				self.msgobj["msgtext"]="\n".join(source[5:])
			else:
				self.msgobj["repto"]=""
				self.msgobj["msgtext"]="\n".join(source[4:])
		except:
			self.msgobj["repto"]=""
			self.msgobj["msgtext"]=""
	
	def getMsg_From_Visual(self):
		self.msgobj["echoarea"]=self.lineEdit.text()
		self.msgobj["subj"]=self.lineEdit_2.text()
		self.msgobj["to"]=self.lineEdit_4.text()
		self.msgobj["repto"]=self.lineEdit_3.text()
		self.msgobj["msgtext"]=self.plainTextEdit_1.toPlainText()
	
	def updateSource(self):
		msgobj=self.msgobj

		source=msgobj["echoarea"]+"\n"+msgobj["to"]+"\n"+msgobj["subj"]+"\n\n"
		
		if msgobj["repto"]!="":
			source+="@repto:"+msgobj["repto"]+"\n"
		
		source+=msgobj["msgtext"]

		self.plainTextEdit.setPlainText(source)
	
	def updateVisual(self):
		self.lineEdit.setText(self.msgobj["echoarea"])
		self.lineEdit_2.setText(self.msgobj["subj"])
		self.lineEdit_4.setText(self.msgobj["to"])
		self.lineEdit_3.setText(self.msgobj["repto"])
		self.plainTextEdit_1.setPlainText(self.msgobj["msgtext"])
	
	def tabChanged(self, index):
		if index==0:
			self.getMsg_From_Source()
			self.updateVisual()
		elif index==1:
			self.getMsg_From_Visual()
			self.updateSource()
	
	def saveFile(self):
		index=self.tabWidget.currentIndex()
		if index==0:
			self.getMsg_From_Visual()
			self.updateSource()
		elif index==1:
			self.getMsg_From_Source()

		string=self.plainTextEdit.toPlainText()

		try:
			f=open(self.filename, "wb")
			f.write(string.encode("utf8"))
			f.close()
		except:
			self.mbox.setText("Файл "+self.filename+" сохранить не удалось =(")
			self.mbox.exec_()
	
	def closeAndDelete(self):
		self.mbox.setText("Точно удалить сообщение и выйти?")
		self.mbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
		result=self.mbox.exec_()

		if result==QtWidgets.QMessageBox.Yes:
			os.remove(self.filename)
			self.close()
	
	def closeWithoutSaving(self):
		self.close()

if len(sys.argv[1:])>0:
	app = QtWidgets.QApplication(sys.argv)
	form=EditorForm(sys.argv[1])
	form.show()
	sys.exit(app.exec_())
else:
	print("Требуется имя файла!")
