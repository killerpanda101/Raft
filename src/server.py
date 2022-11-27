from socket import *
import threading
import sendRecv as utils
from key_value_store import KeyValueStore
from config import server_nodes
import ast

class Server:
    def __init__(self, name, port=10000):
        self.port = port
        self.name = name
        self.kvs = KeyValueStore(server_name=self.name)
        self.kvs.catch_up()

    # Hi server say hi to your new friends!
    def destination_addresses(self):
        other_servers = {k: v for (k, v) in server_nodes().items() if k != self.name}
        return list(other_servers.values())

    def address_of(self, server_name):
        return server_nodes()[server_name]

    # Send messages to friend!
    def tell(self, message, to_server_address):
        print(f"connecting to {to_server_address[0]} port {to_server_address[1]}")

        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect(to_server_address)

        try:
            print(f"sending {message}")
            utils.Send(self.client_socket, message.encode('utf-8'))
        except:
            print(f"closing socket")
            self.client_socket.close()


    # setting up a listening socket!
    def start(self):
        server_address = ('localhost', self.port)

        f = open("server_registry.txt", "a")
        f.write(self.name + " localhost " + str(self.port) + '\n')
        f.close()

        print("starting up on " + str(server_address[0]) + " port "  + str(server_address[1]))

        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_socket.bind(server_address)
        self.server_socket.listen(1)

        while True:
            try:
                # accept new connection and spawn thread
                connection, client_address = self.server_socket.accept()
                print(f"connection from {client_address}")
                threading.Thread(target=self.handle_client, args=(connection, self.kvs)).start()
            
            except:
                # close an exit if errors
                if(connection):
                    connection.close()
                break

    
    def handle_client(self, connection, kvs):
        while True:
            # read data from socket
            raw_data = utils.Recv(connection)
            server_id, data = self.return_address_and_message(raw_data)
            
            print(f"Recieved operation {data}")
            
            
            res = ''

            # request log length
            if(data == "log_length?"):
                res = "log_length"+str(len(self.kvs.log))
            
            # leader sending catch-up info
            elif data.split(" ")[0] == "log_length":
                catchUpIdx = int(data.split(" ")[1])
                if len(self.kvs.log) > catchUpIdx:
                    res = "catch_up_log "+str(self.kvs.log[catchUpIdx:])
                else:
                    res = "Your info is as good as mine!"

            # follower applying catch logs
            elif data.split(" ")[0] == "catch_up_log":
                logsToAppend = ast.literal_eval(data.split("catch_up_log ")[1])
                [self.kvs.execute for log in logsToAppend]
                res = "Caught up. Thanks!"

            # show log (debugging!)
            elif data == "show_log":
                res = str(self.kvs.log)

            # Establish yourself as the leader!
            elif data == "youre_the_leader":
                self.broadcast(self.with_return_address('log_length?'))
            
            # just execute operation
            else:
                res = kvs.execute(data)

            # send response!
            res = self.with_return_address(res)
            utils.Send(connection, res)

    def broadcast(self, message):
        for other_server_address in self.destination_addresses():
            self.tell(message, to_server_address=other_server_address)
                    
    def return_address_and_message(self, string_request):
        address_with_message = string_request.split("@")
        return address_with_message[0], "@".join(address_with_message[1:])

    def with_return_address(self, response):
        return self.name + "@" + response
                        
    

    
    
