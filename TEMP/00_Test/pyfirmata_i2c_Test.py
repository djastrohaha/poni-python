#!/usr/bin/env python
# coding: utf-8

import pyfirmata
from pyfirmata import ArduinoMega, util
import time
import threading, Queue
import json

address = 0x20 # I2C address of MCP23017


class MyBoard(pyfirmata.Board):
	def __init__(self):
		super(MyBoard, self).__init__('COM2')

		self.pinTest = self.get_pin('d:13:p')
		self.pinTest.write(0)


		self.it = util.Iterator(self)
		self.it.start()

		self.testI2CMessage()



		
	def _handle_i2c(self, *data):
	# do your thing
		print "reciving i2c : ",data

	def testI2CMessage(self):

		print "i2c test"

		args1 = [0x70,0x00, 0x00]# Set all of bank A to outputs 
		data1 = [address, 0B00000000]
		for item in args1:
			data1.append(item & 0x7f)
			data1.append((item >> 7) & 0x7f)

		self.send_sysex(pyfirmata.I2C_REQUEST, data1)


		# data2 = bytearray([address, 0x01, 0x00])# Set all of bank B to outputs
		args2 = [0x70,0x01, 0x00]
		data2 = [address, 0B00000000]
		for item in args2:
			data1.append(item & 0x7f)
			data1.append((item >> 7) & 0x7f)
		self.send_sysex(pyfirmata.I2C_REQUEST, data2)



		args3 = [0x70,0x12, 00000011]
		data3 = [address, 0B00000000]
		for item in args3:
			data3.append(item & 0x7f)
			data3.append((item >> 7) & 0x7f)



		self.send_sysex(pyfirmata.I2C_REQUEST, data3)

		self.pinTest.write(1)
		print "i2C over"





if __name__ == "__main__":
	print "ok"

	board = MyBoard()
	board.add_cmd_handler(pyfirmata.I2C_REPLY, board._handle_i2c)