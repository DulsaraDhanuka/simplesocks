import json
import base64
import select
import socket
from typing import List
from cryptography.fernet import Fernet

class SimpleServer():
    def __init__(self, host: str=None, port: int=4444, header_length: int=10, server_key: bytes=None) -> None:
        self._header_length: int = header_length
        if host is None:
            host = socket.gethostbyname(socket.gethostname())
        port: int = port

        self._fernet: Fernet = None
        if server_key is not None:
            self._fernet = Fernet(server_key)

        self._socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((host, port))

        self._connections: List[socket.socket] = [self._socket]
        self._clients = {}

    def _encrypt_data(self, data: bytes) -> bytes:
        if self._fernet is None:
            return base64.b64encode(data)
        
        return self._fernet.encrypt(data)

    def _decrypt_data(self, data: bytes) -> bytes:
        if self._fernet is None:
            return base64.b64decode(data)

        return self._fernet.decrypt(data)

    def _receive_data(self, client_socket: socket.socket):
        try:
            data_header = client_socket.recv(self._header_length)
            if not len(data_header):
                return False
            
            data_length = int(data_header.decode("utf-8").strip())
            data = client_socket.recv(data_length)
            data = self._decrypt_data(data)
            return data
        except:
            return False
    
    def _send_data(self, socket: socket.socket, data: bytes) -> None:
        data = self._encrypt_data(data)
        data = f"{len(data):<{self._header_length}}".encode("utf-8") + data
        socket.send(data)

    def listen(self) -> None:
        self._socket.listen()

        while True:
            if len(self._connections) == 0:
                print("Shutting down server")
                break
            read_sockets, _, exception_sockets = select.select(self._connections, [], self._connections)

            for notified_socket in read_sockets:
                if notified_socket == self._socket:
                    client_socket, client_address = self._socket.accept()

                    initialization_data = self._receive_data(client_socket)
                    if initialization_data is False:
                        continue

                    self.accept_client_connection(client_socket, client_address, initialization_data)
                else:
                    data = self._receive_data(notified_socket)

                    if data is False:
                        self.close_client_connection(self._clients[notified_socket], notified_socket)
                        continue

                    self.handle_incoming_data(self._clients[notified_socket], notified_socket, data)

            for notified_socket in exception_sockets:
                self.close_client_connection(self._clients[notified_socket], notified_socket)

    def send_client_data(self, client_socket: socket.socket, data: bytes) -> None:
        self._send_data(client_socket, data)

    def terminate_server(self) -> None:
        for connection in reversed(self._connections):
            connection.close()
        self._connections = []
        self._clients = {}

    def broadcast_data(self, sender: socket.socket, data: bytes, clients: List[socket.socket]=None) -> None:
        if clients is None:
            clients = self._clients.keys()
        
        for client in clients:
            if client == sender:
                continue
            
            self.send_client_data(client, data)

    def accept_client_connection(self, client_socket: socket.socket, client_address: tuple, initialization_data: object) -> None:
        self._connections.append(client_socket)
        self._clients[client_socket] = json.loads(initialization_data.decode("utf-8"))['id']

    def handle_incoming_data(self, client_id: str, client_socket: socket.socket, data: bytes) -> None:
        pass

    def close_client_connection(self, client_id: str, client_socket: socket.socket) -> None:
        client_socket.close()
        self._connections.remove(client_socket)
        del self._clients[client_socket]
