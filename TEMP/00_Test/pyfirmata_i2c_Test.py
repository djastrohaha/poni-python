#!/usr/bin/env python
# coding: utf-8

import pyfirmata
from pyfirmata import util
import time



address = 0x20 # I2C address of MCP23017

IODIRA = 0x00   # Pin direction register
IODIRB = 0x01   # Pin direction register
OLATA  = 0x14   # Register A for outputs
OLATB  = 0x15   # Register B for outputs
GPIOA  = 0x12   # Register A for inputs
GPIOB  = 0x13   # Register B for inputs

class MyBoard(pyfirmata.Board):
	def __init__(self):
		super(MyBoard, self).__init__('COM2')

		self.pinTest = self.get_pin('d:13:p')
		self.pinTest.write(0)

		
		self.it = util.Iterator(self)
		self.it.start()

		self.send_sysex(pyfirmata.I2C_REQUEST, [address,IODIRA,0x00])
		self.send_sysex(pyfirmata.I2C_REQUEST, [address,IODIRB,0x00])

		
	def _handle_i2c(self, *data):
	# do your thing
		print "reciving i2c : ",data

	def testI2CMessage(self):

		print "i2c test"

		# args1 = [0x70,0x00, 0x00]# Set all of bank A to outputs 
		# data1 = [address, 0B00000000]
		# for item in args1:
		# 	data1.append(item & 0x7f)
		# 	data1.append((item >> 7) & 0x7f)

		# self.send_sysex(pyfirmata.I2C_REQUEST, data1)


		while 1:
		
			self.send_sysex(pyfirmata.I2C_REQUEST, [address,OLATA,0xff])
			self.send_sysex(pyfirmata.I2C_REQUEST,[address,OLATB,0xff])

			self.pinTest.write(1)

			time.sleep(1)

			self.send_sysex(pyfirmata.I2C_REQUEST, [address,OLATA,0x00])
			self.send_sysex(pyfirmata.I2C_REQUEST,[address,OLATB,0x00])

			self.pinTest.write(0)

			time.sleep(1)
			print "---"
		print "i2C over"


		




if __name__ == "__main__":
	print "ok"

	board = MyBoard()
	board.add_cmd_handler(pyfirmata.I2C_REPLY, board._handle_i2c)
	board.testI2CMessage()