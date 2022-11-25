import socket
import sendRecv as utils
from key_value_store import KeyValueStore

# setting up a listening socket!
def server_setup():
    server_address = ('localhost', 10000)
    print(f"starting up on {server_address[0]} port {server_address[1]}")

    sock = socket.socket()
    sock.bind(server_address)
    sock.listen(1)

    return sock

# bring the key value store upto spec!
def catch_up(key_value_store):
    f = open("commands.txt", "r")
    log = f.read()
    f.close()

    for command in log.split('\n'):
        key_value_store.execute(command)


def main():
    kvs = KeyValueStore()
    catch_up(kvs)
    sock = server_setup()
    
    while True:
        try:
            print('waiting for a connection')
            # accept new connection
            connection, client_address = sock.accept()
            print(f"connection from {client_address}")

            # read data from socket
            data = utils.Recv(connection)
            print(f"Recieved operation {data}")

            # write operation to file
            f = open("commands.txt", "a")
            f.write(data + '\n')
            f.close()
                
            # execute operation and send response
            res = kvs.execute(data)
            utils.Send(connection, res)
                        
        except:
            if(connection):
                connection.close()
            break

main()