import collections, json, selectors, socket, _thread, socketserver, simpleaudio as sa
from threading import Thread
from multiplex import recv, send
from server2 import Server
from server_udp import ServerUDP
NUM_PARTICIPANTS = 256

class RoomServer:

    def __init__(self):
        self.Keep_running = True
        self.server_socket_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket_TCP.bind(('192.168.1.3', 0))
        self.server_address_TCP = self.server_socket_TCP.getsockname()
        self.server_socket_TCP.listen(NUM_PARTICIPANTS)
        self.server_socket_TCP.setblocking(False)

        self.selector_TCP = selectors.DefaultSelector()
        self.selector_TCP.register(fileobj=self.server_socket_TCP,
                               events=selectors.EVENT_READ,
                               data=self.on_accept_TCP)

        # self.server_socket_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.server_socket_UDP.bind(('192.168.1.3', 0))
        # self.server_address_UDP = self.server_socket_UDP.getsockname()
        # self.server_socket_UDP.receive(NUM_PARTICIPANTS)
        # self.server_socket_UDP.setblocking(False)

        # self.selector_UDP = selectors.DefaultSelector()
        # self.selector_UDP.register(fileobj=self.server_socket_UDP,
        #                        events=selectors.EVENT_READ,
        #                        data=self.on_accept_UDP)
        # # Keeps track of the peers currently connected. Maps socket fd to
        # # peer name, ID.
        self.connections_msg_queue = {}

    def get_ports(self):
        return self.server_address_TCP

    def on_accept_TCP(self, sock, mask):
        conn, addr = self.server_socket_TCP.accept()
        print("accepted")
        conn.setblocking(False)
        self.connections_msg_queue[conn] = collections.deque()
        self.selector_TCP.register(conn, selectors.EVENT_READ, self.read)
    
    # def on_accept_UDP(self, sock, mask):
    #     conn, addr = self.server_socket_UDP.accept()
    #     conn.setblocking(False)
    #     self.connections_msg_queue[conn] = collections.deque()
    #     self.selector_UDP.register(conn, selectors.EVENT_READ, self.read)

    def read(self, conn, mask):
        
        data = recv(conn)
        if data :
            print("Reading")
            self.add_msg( conn, data ) #should add checking the header
            
        else:
            print("Removing")
            self.remove_participant(conn)
    
    def remove_participant(self, conn):
        
        self.selector_TCP.unregister(conn)
        # else:
        #     self.selector_UDP.unregister(conn)
        conn.close()
        del self.connections_msg_queue[conn]
        if not bool(self.connections_msg_queue):
            self.Keep_running = False

    def add_msg( self, conn, msg):
        for connection, messages in self.connections_msg_queue.items():
            if connection != conn:
                conn.setblocking(False)  # not sure if needed
                # if conn.socketType == socket.SOCK_STREAM:
                self.selector_TCP.modify(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, self.read_write)
                # else:
                #     self.selector_UDP.modify(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, self.read_write)
                messages.append(msg)

    def read_write(self, conn, mask):
        if mask & selectors.EVENT_READ:
            self.read(conn, mask)
        if mask & selectors.EVENT_WRITE:
            self.write(conn, mask)

    def write(self, conn, mask):
        messages = self.connections_msg_queue[conn]
        while messages:
            msg = messages.popleft()
            try:
                send(conn, msg)
            except Exception as e:
                print('Error occurred', e)
                self.remove_participant(conn)
                return

        # if no more message to send, don't listen to available for write
        conn.setblocking(False)  # not sure if needed
        self.selector_TCP.modify(conn, selectors.EVENT_READ, self.read)

    def run_TCP(self):
        while self.Keep_running:
           events = self.selector_TCP.select()
           for key, mask in events:
               callback = key.data
               callback(key.fileobj, mask)
        
        self.selector_TCP.close()
    
    # def run_UDP(self):
    #     while bool(self.connections_msg_queue):
    #        events = self.selector_UDP.select()
    #        for key, mask in events:
    #            callback = key.data
    #            callback(key.fileobj, mask)
        
    #     self.selector_UDP.close()
    
    def stop(self):
        self.Keep_running = False

    def run(self):
        # _thread.start_new_thread(self.run_TCP())
        # _thread.start_new_thread(self.run_UDP())
        self.run_TCP()

# The above code is just the server specific for the room, not the basic server itself

class TCPMainServer(socketserver.BaseRequestHandler):
    rooms = {}
    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = recv(self.request, decode= False).decode("utf-8")
        data = self.data.split()
        if data[0] == "Create":
            existingRooms = self.rooms.keys()
            print(data[1], existingRooms)
            if data[1] in existingRooms:
                print(self.rooms[data[1]][0].is_alive())
            if data[1] in existingRooms and self.rooms[data[1]][0].is_alive():
                port = 65536
                port_byte = port.to_bytes(4, 'big')
                print("Room already exists")
                send(self.request, port_byte, encode= False)
            else:
                roomserver = ServerUDP()
                # _thread.start_new_thread(roomserver.run())
                t = Thread(target= roomserver.run)
                t.start()
                print(t)
                port = roomserver.get_ports()[1]
                self.rooms[data[1]] = [t, data[2], port]
                port_byte = port.to_bytes(4, 'big')
                send(self.request, port_byte, encode= False)
                print("Created Room")
        if data[0] == "Join":
            existingRooms = self.rooms.keys()
            roomName = data[1]
            passwd = data[2]
            print("Join Request ", roomName)
            if roomName in existingRooms and self.rooms[roomName][0].is_alive() and self.rooms[roomName][1] == passwd:
                port = self.rooms[roomName][2]
                port_byte = port.to_bytes(4, 'big')
                send(self.request, port_byte, encode= False)
                print("Join Room")
            else:
                port = 65536
                port_byte = port.to_bytes(4, 'big')
                send(self.request, port_byte, encode= False)

if __name__ == "__main__":
    HOST, PORT = "192.168.1.4", 9998

    # Create the server, binding to localhost on port 9999
    with socketserver.TCPServer((HOST, PORT), TCPMainServer) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        server.serve_forever()

