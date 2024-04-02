import socket
import threading
import json

class ChatRoomDirectoryServer:
    def __init__(self, port):
        self.chat_room_directory = {} # Format: {'room_name': {'address': 'multicast_ip', 'port': port}, ...}
        self.address =[]
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', port))
        self.server_socket.listen(5)
        print(f"Chat Room Directory Server listening on port {port}...")

    def handle_client_commands(self, client_socket, client_address):
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                command = data.decode('utf-8').split()
                if command[0] == 'getdir':
                    client_socket.send(json.dumps(self.chat_room_directory).encode('utf-8'))
                elif command[0] == 'makeroom' and len(command) == 4:
                    room_name, address, port = command[1], command[2], int(command[3])
                    if room_name not in self.chat_room_directory and (address not in self.address):
                        self.chat_room_directory[room_name] = {'address': address, 'port': port}
                        self.address.append(address)
                        print(address, self.address)
                        client_socket.send(f"Room '{room_name}' created.".encode('utf-8'))
                    else:
                        client_socket.send("Room already exists.".encode('utf-8'))

                elif command[0] == 'deleteroom' and len(command) == 2:
                    room_name = command[1]
                    if room_name in self.chat_room_directory:
                        self.address.remove(self.chat_room_directory[room_name]['address'])
                        del self.chat_room_directory[room_name]
                        client_socket.send(f"Room '{room_name}' deleted.".encode('utf-8'))
                    else:
                        client_socket.send("Room does not exist.".encode('utf-8'))
                else:
                    client_socket.send("Invalid command.".encode('utf-8'))
            except Exception as e:
                print(f"Error with client {client_address}: {e}")
                break
        print(f"Client {client_address}Disconnected")
        client_socket.close()

    def accept_connections(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Accepted connection from {client_address}.")
            threading.Thread(target=self.handle_client_commands, args=(client_socket, client_address)).start()

if __name__ == "__main__":
    server_port = 11111
    crds = ChatRoomDirectoryServer(server_port)
    crds.accept_connections()
