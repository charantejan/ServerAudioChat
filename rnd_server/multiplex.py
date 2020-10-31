from socket import socket as Socket
from select import select
from json import loads, dumps

def recv(socket: Socket, decode=False):
    '''
    Receives a python object in stream
    decode: decodes using json
    returns None if connection is closed
    '''
    length = b''
    while len(length) < 4:
        chunk = socket.recv(4 - len(length))
        # print("here3", chunk)
        if chunk == b'':
            print("here")
            return None
        length += chunk
    length = int.from_bytes(length, 'big')
    print(length)
    received = 0
    chunks = []
    while received < length:
        print(received, "here1234")
        chunk = socket.recv(length - received)
        # print(chunk, "here1")
        if chunk == b'':
            return None
        chunks.append(chunk)
        received += len(chunk)
    # print("here2")
    data = b''.join(chunks)
    if decode:
        data = loads(data)
        # NOTE if data is None, it is assumed that socket is disconnected
    return data


def send(socket: Socket, data, encode=False):
    '''
    Sends a python object in stream.
    encode: encodes using json
    '''
    if encode:
        data = dumps(data).encode('utf-8')
    # print(len(data).to_bytes(4, 'big'))
    data = len(data).to_bytes(4, 'big') + data
    print("sending")
    socket.sendall(data)
