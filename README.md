# Simplesocks

A simple socket wrapper for python built on top of the standard socket library with password based encryption for security.

## Instructions 

1. Install 

```bash
pip install simplesocks
```

2. Create server.py

```python
import socket
from simplesocks.server import SimpleServer
import json

class TestServer(SimpleServer):
    def accept_client_connection(self, client_socket: socket.socket, client_address: tuple, initialization_data: object) -> None:
        super().accept_client_connection(client_socket, client_address, initialization_data)

        initialization_data = json.loads(initialization_data)['id']
        print(f"Client {client_address[0]}:{client_address[1]} connected as {initialization_data}")

    def handle_incoming_data(self, client_id: str, client_socket: socket.socket, data: bytes) -> None:
        super().handle_incoming_data(client_id, client_socket, data)

        if data == b"TERMINATE":
            print(f"Server termination requested by {client_id}")
            self.terminate_server()
        
        self.broadcast_data(client_socket, json.dumps({'id': client_id, 'data': data.decode()}).encode('utf-8'))

    def close_client_connection(self, client_id: str, client_socket: socket.socket) -> None:
        super().close_client_connection(client_id, client_socket)
        print(f"Client {client_id} disconnected")

server = TestServer(server_key=b"msZ5ZR9zjtBXRzssQ3qD33FAVxTBir55rHa1dAJlV5g=")
server.listen()
```

3. Create client.py

```python
import json
import threading
import time
from simplesocks.client import SimpleClient, ClientReceiveDataTimeoutException

client = SimpleClient('192.168.1.200', 4444, server_key=b"msZ5ZR9zjtBXRzssQ3qD33FAVxTBir55rHa1dAJlV5g=")

def receive():
    while True:
        try:
            message = json.loads(client.receive_data().decode('utf-8'))
            print(f"{message['id']}: {message['data']}")
        except ClientReceiveDataTimeoutException as e:
            continue
def write():
    while True:
        client.send_data(input("").encode('utf-8'))

receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()
```

4. Start the server

```
python server.py
```

5. Connect with client instances

```
python client.py
```
