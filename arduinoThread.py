#!/usr/bin/env python
# coding: utf-8

import pyfirmata
# from pyfirmata import ArduinoMega, util
import time
import threading, Queue
import json

port = 'COM2'



# je communique entre la page web, le serveur web et le monitor grace à des dictionnaires (en python) 
#qui sont la même chose qu'un objet JSON en java (si ceci à un sens).et que l'on peut convertir grace au module python json
#dico type:
# {'action':actionName, "tasks":{"task1":value1, "task2":value2}}
#les noms de taches task1, task2, etc, sont directement le nom des pins dont il faut changer une valeure



#pour faire propre il faudra compacter un une seule classe les classes MyBoard et ArduinoConnection
#je testai juste l'implémentation de l'i2c, mais ça marche pas.... je dois me planter dans le message que j'envoie
#c'est chaud...

class MyBoard(pyfirmata.Board):
	def __init__(self):
		super(MyBoard, self).__init__(port)
		self.pinTest = self.get_pin('d:13:p')
		self.pinTest.write(0)
		
	def _handle_i2c(self, *data):
	# do your thing
		print data

	def testI2CMessage(self):
		address = 0x20 # I2C address of MCP23017

		print "i2c test"
		data1 = [address,0x00,0x00]# Set all of bank A to outputs 
		self.send_sysex(pyfirmata.I2C_REQUEST, data1)

		data2 = [address,0x01,0x00]# Set all of bank B to outputs
		self.send_sysex(pyfirmata.I2C_REQUEST, data2)

		data3 = [address, 0x14, 0x01]#switching bank A (0x14) to 1 (0x01)

		self.send_sysex(pyfirmata.I2C_REQUEST, data3)

		self.pinTest.write(1)
		print "i2C over"



class ArduinoConnection(object):
	def __init__(self):
		# self.port = 'COM2'
		self.boardConnected = False

		self.pinDict = {}
		
		try:
			# self.board = ArduinoMega(self.port)
			self.board = MyBoard()
			self.board.add_cmd_handler(pyfirmata.I2C_REPLY, self.board._handle_i2c)


			print 'Connected to Arduino, wait for 2s'
			time.sleep(2)
			self.boardConnected = True
			
		except:
			print "Arduino missing on %s" %port


		if self.boardConnected:
			#staring pyfirmata iterator for correct board update
			self.it = pyfirmata.util.Iterator(self.board)
			self.it.start()
			print 'iterator started'
			
			# defining pins
			self.LED = self.board.get_pin('d:2:p')
			
			self.lightTest = self.board.get_pin('a:2:i')
			self.lightTest.enable_reporting()

			self.pinDict = {"ECLight":self.LED,
							 "ECLightDetector":self.lightTest}


			#en cours de test mais ça marche pas putain!
			self.board.testI2CMessage()

	def isConnected(self):
		if  self.boardConnected:
			return True
		else:
			return False


	def getBoardValues(self, values):
		valuesDict = {}

		for v in values:

			pin = self.pinDict[v]
			result = pin.read()
			valuesDict.setdefault(v, result)

		return valuesDict


	def runtasks(self, task):
		#changing pin value
		for k in task.keys():

			pin = self.pinDict[k]
			pin.write(task[k])


class ECModule(threading.Thread):
	#classe type pour un module
	#thread séparé mis a jour par le thread monitor general et qui envoie des taches 
	#dans la queue de taches à destination de l'arduino
	def __init__(self, taskQ):
		super(ECModule, self).__init__()
		self.setDaemon(True)

		self.globalTaskQ = taskQ

		self.MINVALUE = 0.25

		self.lightState = 0
		self.lightValue = 0


	def run(self):

		while True:
			print 'ECLightDetector', self.lightValue, self.lightState

			if self.lightValue < self.MINVALUE and self.lightState == 0:
				self.globalTaskQ.put({"action":"board","tasks":{"ECLight":1}})
				timeOffset = 2

			elif self.lightValue < self.MINVALUE and self.lightState == 1:
				timeOffset = 2

			elif self.lightValue >= self.MINVALUE and self.lightState == 1:
				self.globalTaskQ.put({"action":"board","tasks":{"ECLight":0}})
				timeOffset = 1

			time.sleep(timeOffset)#eviter de mettre un time offset < à celui du boardmonitorloop: j'imagine que le taskQ va saturer



class BoardMonitorLoop(threading.Thread):
	#classe du monitor general
	#il envoie les taches de taskQ à l'arduino et
	#ecoute/met à jour les valeurs relevées sur les pins
	#si il doit renvoyer quelque chose vers la page web il le fait via resultQ (cf: def checkResults, dans la fonction main du server)
	def __init__(self, taskQ, resultQ):
		super(BoardMonitorLoop, self).__init__()
		
		self.taskQ = taskQ
		self.resultQ = resultQ
		
		self.valuesToUpdate = []

		self.board = ArduinoConnection()

		if self.board.isConnected():
			self.EC = ECModule(self.taskQ)
			self.EC.start()

			#les autres modules seront à ajouter ici (ph etc...)
		

				
	def updateFromBoard(self):

		boardValues = self.board.getBoardValues(["ECLightDetector", "ECLight"])
		print boardValues
		self.EC.lightState = boardValues["ECLight"]
		self.EC.lightValue = boardValues["ECLightDetector"]


		valuesToSend = {}
		valuesToSend.setdefault("ECLightDetector", boardValues["ECLightDetector"])

		self.sendValuesToTornado(valuesToSend)


	def dispatchTask(self, task):
		print task
		if isinstance(task, dict):
			taskDict = task	
		else:
			taskDict = json.loads(task)

		action = taskDict["action"]
		print "action", action
		if action == "board":

			self.board.runtasks(taskDict["tasks"])

		elif action == "hasBoard":
			if self.board.isConnected():
				message = {"log":"Board connected!"}
			else:
				message = {"log":"Board missing!"}

			self.sendValuesToTornado(message)


	def run(self):
			
		while 1:
			# getting tasks from web server to arduino
			if not self.taskQ.empty():

				task = self.taskQ.get()
				print "in run loop: ", task
				self.dispatchTask(task)
				

			if self.board.isConnected():
			#sending tasks from arduino to web server
				self.updateFromBoard()
			
			time.sleep(0.5) #updateData every 1/2 seconds
	

	def sendValuesToTornado(self, values):
		# print "sending to tornado" , values
		self.resultQ.put(json.dumps(values))

	
