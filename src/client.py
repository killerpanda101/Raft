import socket
import sys
import sendRecv as utils

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
server_address = ('localhost', 10000)
print(f"connecting to {server_address[0]} port {server_address[1]}")
sock.connect(server_address)

try:
    # Send data
    message = input("Type your message:\n")
    print(f"sending {message}")
    utils.Send(sock, message)
    
    # Receive response
    res = utils.Recv(sock)
    print(f'recieved: {res}')
    
finally:
    print(f"closing socket")
    sock.close()