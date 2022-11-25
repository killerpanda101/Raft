import socket
import sys
import src.utils.sendRecv

# Our very own 
keyValueStore = {}

def get(key):
    return keyValueStore[key]

def set(key, value):
    keyValueStore[key] = value

def delete(key):
    del keyValueStore[key]

# setting up a listening socket!
def server_setup():

    server_address = ('localhost', 10000)
    print(f"starting up on {server_address[0]} port {server_address[1]}")

    sock = socket.socket()
    sock.bind(server_address)

    sock.listen(1)

    return sock

# parse input and return output.
def performOperation(data):
    
    # this is such a nice trick!
    command, key, value = 0,1,2
    
    operationString = data.decode("utf-8")
    operation = operationString.split(" ")

    response = "Sorry, I don't understand that command :-("

    if operation[command] == "get":
        response = get(operation[key])
    elif operation[command] == "set":
        set(operation[key], operation[value])
        response = f"key {operation[key]} set to {operation[value]}"
    elif(operation[command] == "delete"):
        delete(operation[key])
        response = f"Key operation[key] was deleted!"
    elif(operation[command] == "show"):
        response = str(keyValueStore)
    else:
        pass

    return response


def main():

    sock = server_setup()
    
    while True:
        print('waiting for a connection')
        connection, client_address = sock.accept()

        try:
            print(f"connection from {client_address}")

            data = Recv(connection)
            print(f"Recieved operation {data}")
            
            res = performOperation(data)
            Send(connection, res)
                    
        finally:
            # Clean up the connection
            connection.close()

main()