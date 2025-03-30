import json
import socket

class socketclient():
    def __init__(self,host,port):
        self.host = host
        self.port = port
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(1)
        print("Server listening on port", self.port)
        self.conn,self.addr = server.accept()
        print(f"Connected by {self.addr}")

    def send(self,data):
        data = json.dumps(data,ensure_ascii=False,indent=4)
        self.conn.sendall(data.encode())

    def recv(self):
        data = b''
        while True:
            chunk = self.conn.recv(8192)
            if not chunk: break
            data += chunk
            if len(chunk) < 8192: break

        if not data:
            print("Received No return")
            return False
        if data:
            data = json.loads(data)
            print(data)
            return data



