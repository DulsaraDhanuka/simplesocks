import base64
import json
import socket
import sys
import uuid
from cryptography.fernet import Fernet

class ClientReceiveDataTimeoutException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__("Client did not recieve any data", *args)

class SimpleClient():
    def __init__(self, server_host: str, server_port: int, connection_id: str=None, header_length: int=10, server_key: str=None) -> None:
        self._header_length = header_length
        self._connection_id = connection_id
        if self._connection_id is None:
            self._connection_id = str(uuid.uuid4())

        self._fernet: Fernet = None
        if server_key is not None:
            self._fernet = Fernet(server_key.encode('utf-8'))
        
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((server_host, server_port))
        #self._socket.setblocking(False)

        self.send_data(json.dumps({'id': self._connection_id}).encode('utf-8'))

    def _encrypt_data(self, data: bytes) -> bytes:
        if self._fernet is None:
            return base64.b64encode(data)
        
        return self._fernet.encrypt(data)

    def _decrypt_data(self, data: bytes) -> bytes:
        if self._fernet is None:
            return base64.b64decode(data)

        return self._fernet.decrypt(data)

    def send_data(self, data: bytes) -> None:
        data = self._encrypt_data(data)
        header = f"{len(data):<{self._header_length}}".encode('utf-8')
        self._socket.send(header + data)

    def receive_data(self, timeout: float=2) -> bytes:
        self._socket.settimeout(timeout)
        data = None

        try:
            while True:
                header = self._socket.recv(self._header_length)
                if not len(header):
                    print('Connection closed by the server')
                    sys.exit()
                
                data_length = int(header.decode('utf-8').strip())
                data = self._socket.recv(data_length)
                data = self._decrypt_data(data)
                break
        except socket.timeout as e:
            raise ClientReceiveDataTimeoutException()
        
        return data
