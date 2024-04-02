import socket
import threading
import sys
import struct
import uuid
import json

class ChatClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.chat_name = None
        self.thread1 = None
        self.identifier = uuid.uuid4().hex  # Generate a unique identifier for this client

    def send_message(self, message):
        message = f"{self.identifier}:{message}"  # Prefix message with identifier
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.sendto(message.encode('utf-8'), (self.multicast_group, self.multicast_port))

    def connect_to_server(self):
        self.sock.connect((self.server_ip, self.server_port))
        print("Connected to Chat Room Directory Server.")

    def send_command(self, command):
        self.sock.send(command.encode('utf-8'))
        response = self.sock.recv(1024)
        print(response.decode('utf-8'))
        return response

    def listen_for_messages(self, multicast_group, multicast_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind(multicast_port)
        mreq = struct.pack("4sl", socket.inet_aton(multicast_group), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        last_message = None
        while True:
            data, _ = sock.recvfrom(1024)
            message = data.decode('utf-8')
            sender_id, s_message = message.split(':', 1)

            if sender_id != self.chat_name and last_message != message:
                print(message)
            if sender_id == self.chat_name and s_message == " has left the chat room.":
                break
            last_message = message

    def start_chat_mode(self, multicast_group, port):
        server_address = ('', port)
        self.thread1= threading.Thread(target=self.listen_for_messages, args=(multicast_group, server_address))
        self.thread1.start()
        while True:
            message = input()
            if message.lower() == "exit":
                exit_message = f"{self.chat_name}: has left the chat room."
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
                sock.sendto(exit_message.encode('utf-8'), (multicast_group, port))
                break
            if self.chat_name:
                message = f"{self.chat_name}: {message}"

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
            sock.sendto(message.encode('utf-8'), (multicast_group, port))
        self.thread1.join()

    def run(self):
        self.chat_name = input("Enter your name: ").strip()

        while True:
            command = input("> ").strip()
            if command == "bye":
                self.sock.close()
                if self.thread1:
                    self.thread1.join(  )
                sys.exit()

            elif command.startswith("name "):
                print(f"Changing name to {command.split(' ', 1)[1]}")
                self.chat_name = command.split(' ', 1)[1]

            elif command.startswith("chat "):
                chat_room_name = command.split()[1]
                # Fetch chat room details from the server
                response = self.send_command(f"getdir")
                chat_room_directory = json.loads(response.decode('utf-8'))
                if chat_room_name in chat_room_directory:
                    chat_room = chat_room_directory[chat_room_name]
                    self.start_chat_mode(chat_room['address'], chat_room['port'])
                else:
                    print(f"Chat room '{chat_room_name}' does not exist.")
                # chat_mode_command = input("Enter multicast IP and port separated by space: ").strip()
                # multicast_ip, multicast_port = chat_mode_command.split()
                # self.start_chat_mode(multicast_ip, int(multicast_port))
            else:
                self.send_command(command)

if __name__ == "__main__":
    client_ip = input("Enter server IP: ").strip()
    client_port = int(input("Enter server Port: ").strip())
    client = ChatClient(client_ip, client_port)
    client.connect_to_server()
    client.run()
