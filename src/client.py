import socket
import sendRecv as utils

class Client:
    def __init__(self, server_port=10000):
        self.server_port = server_port

    def start(self):
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = ('localhost', self.server_port)
        print(f"connecting to {server_address[0]} port {server_address[1]}")
        sock.connect(server_address)

        while True:
            try:
                # Send data
                message = input("Type your message:\n")
                print(f"sending {message}")
                utils.Send(sock, message)
                
                # Receive response
                res = utils.Recv(sock)
                print(f'recieved: {res}')
                
            except:
                print(f"closing socket")
                sock.close()