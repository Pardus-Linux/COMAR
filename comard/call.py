#!/usr/bin/python

from qt import *
import socket
import sys

class MainWindow(QMainWindow):
	def __init__(self, *args):
		QMainWindow.__init__(self, *args)
		self.setCaption("Comar Console")
		self.setMinimumSize(540,320)
		vb = QVBoxLayout(self, 6)
		self.result = QTextEdit(self)
		vb.addWidget(self.result)
		self.cmd = QTextEdit(self)
		vb.addWidget(self.cmd)
		self.connect(self.cmd, SIGNAL("returnPressed()"), self.send_data)
	
	def start(self):
		try:
			self.s = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
			self.s.connect("/tmp/comar")
			self.notifier = QSocketNotifier(self.s.fileno(), QSocketNotifier.Read)
			self.notifier.setEnabled(True)
			self.connect(self.notifier, SIGNAL("activated(int)"), self.recv_data)
		except:
			print "cannot connect to comar"
			sys.exit(1)
	
	def recv_data(self):
		data = self.s.recv(256)
		old = self.result.text()
		self.result.setText(str(old) + "\n" + data)
	
	def send_data(self):
		data = str(self.cmd.text())
		self.cmd.setText("")
		self.s.send(data)

if __name__ == "__main__":
	app = QApplication(sys.argv)
	app.connect(app, SIGNAL("lastWindowClosed()"), app, SLOT("quit()"))
	w = MainWindow()
	w.show()
	w.start()
	app.exec_loop()
