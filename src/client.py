import socket

from src.message_passing import send_message, receive_message


class Client:
    def __init__(self, ip, server_port=10000):
        self.ip=ip
        self.server_port = server_port

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_address = (self.ip, self.server_port)
        print(f"connecting to {server_address[0]} port {server_address[1]}")
        self.sock.connect(server_address)

        running = True
        while running:
            try:
                message = input("Type your message:\n")
                messageWithHeader = "client@" + message
                print(f"sending {messageWithHeader}")

                send_message(self.sock, messageWithHeader.encode('utf-8'))

                data = receive_message(self.sock)
                print(f"received {data}")

            except Exception as e:
                print(e)
                # always close the socket to ensure that other 
                # clients can connect to this port later.
                print(f"closing socket")
                self.sock.close()
                running = False







