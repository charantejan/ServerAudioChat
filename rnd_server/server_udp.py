import socket, simpleaudio as sa
import threading, queue
from multiplex import *
class ServerUDP:
	def __init__(self):
		while 1:
			try:
				self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				self.s.bind(('192.168.1.4', 0))
				self.clients = set()
				self.recvPackets = queue.Queue()
				break
			except:
				print("Couldn't bind to that port")

	def get_ports(self):
		return self.s.getsockname()

	def RecvData(self):
		while True:
			data,addr = self.s.recvfrom(1600)
			# print(addr, "read", data)
			self.recvPackets.put((data,addr))

	def run(self):
		threading.Thread(target=self.RecvData).start()

		while True:
			while not self.recvPackets.empty():
				data,addr = self.recvPackets.get()
				y = list(addr)
				y[1] = 5000
				addr = tuple(y)
				self.clients.add(addr)
				if data:
					for c in self.clients:
						if c!=addr:
							self.s.sendto(data,c)
							print("send")
				else:
					self.clients.remove(addr)
		self.s.close()

	def close(self):
		self.s.close()