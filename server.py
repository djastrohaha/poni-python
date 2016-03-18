#!/usr/bin/python27
# coding: utf-8

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.gen
from tornado.options import define, options
 
import time, threading, Queue, os
import json
import arduinoThread

define("port", default=8080, help="run on the given port", type=int)
 
clients = []
root = os.path.dirname(__file__)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.redirect('/home')


class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('home.html')

 
class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
		print 'new connection'
		clients.append(self)
		self.write_message(json.dumps({"log":"connected to socket!"}))

		task = {"action":"hasBoard"}
		q = self.application.settings.get('queue')
		q.put(task)
		print "demande de board..."
 
    def on_message(self, message):
		print 'tornado received from client: %s' % message
		self.write_message(json.dumps({"log":"got it!"}))

		q = self.application.settings.get('queue')
		q.put(message)
 
    def on_close(self):
        print 'connection closed'
        clients.remove(self)
 
################################ MAIN ################################
 
 
def Main():
	
	taskQ = Queue.Queue()
	resultQ = Queue.Queue()
	
	boardMonitorThread = arduinoThread.BoardMonitorLoop(taskQ, resultQ)
	boardMonitorThread.setDaemon(True)
	boardMonitorThread.start()
	
	# wait a second before sending first task
	# time.sleep(1)
	# taskQ.put("first task")
 
	tornado.options.parse_command_line()
	app = tornado.web.Application(
		handlers=[
			(r"/", IndexHandler),
			(r"/home", HomeHandler),
			(r"/ws", WebSocketHandler)
		], queue=taskQ,
		static_path=os.path.join(root, 'static'),
		template_path=os.path.join(root, "template"),
	)
	httpServer = tornado.httpserver.HTTPServer(app)
	httpServer.listen(options.port, address='0.0.0.0')
	print "Listening on port:", options.port
	#tornado.ioloop.IOLoop.instance().start()
 
 
 
	def checkResults():
		#fonction d'envoie de donnée vers la page web via websocket
		if not resultQ.empty():
			result = resultQ.get()
			print "tornado received from arduino: " + result
			for c in clients:
				c.write_message(result)
				
	
	mainLoop = tornado.ioloop.IOLoop.instance()
	scheduler = tornado.ioloop.PeriodicCallback(checkResults, 10, io_loop = mainLoop)
	scheduler.start()
	mainLoop.start()
		
 
if __name__ == "__main__":
	
	mainThread =  threading.Thread(target=Main())
	
	mainThread.start()
	
	
	