import socket, simpleaudio as sa
import threading
from multiplex import *
class Server:
    def __init__(self):
            while 1:
                try:
                    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.s.bind(('192.168.1.4', 0))

                    break
                except:
                    print("Couldn't bind to that port")

            self.connections = []

    def get_ports(self):
        return self.s.getsockname()

    def accept_connections(self):
        self.s.listen(100)
        
        while True:
            c, addr = self.s.accept()

            self.connections.append(c)

            threading.Thread(target=self.handle_client,args=(c,addr,)).start()
        
    def broadcast(self, sock, data):
        for client in self.connections:
            if client != self.s and client != sock:
                try:
                    send(client, data)
                except:
                    pass

    def remove(self, c):
    	if c in connections: 
            connections.remove(c) 

    def handle_client(self,c,addr):
        while 1:
            try:
                data = c.recv(1024)
                if data:
                	sa.play_buffer(data,2,2,44100)
                	self.broadcast(c, data)
                	print("Read")

                else:
                	self.remove(c)
                	c.close()
                	break
            
            except:
                continue
    def run(self):
        self.accept_connections()