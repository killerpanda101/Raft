import time
import os
import threading

class KeyValueStore:
    client_lock = threading.Lock()

    def __init__(self, server_name):
        self.server_name = server_name
        self.data = {}
        self.log = []

    def get(self, key):
        return self.data[key]

    def set(self, key, value):
        self.data[key] = value

    def delete(self, key):
        del self.data[key]

    def execute(self, operationStr):
        # write command to file and append to log!
        self.log.append(operationStr)
        f = open(self.server_name + "_log.txt", "a+")
        f.write(operationStr + '\n')
        f.close()
        
        command, key, value = 0,1,2 # Nice trick!
        operation = operationStr.split(" ")

        response = "Sorry, I don't understand that command :-("

        with self.client_lock:
            if operation[command] == "get":
                response = self.get(operation[key])
            elif operation[command] == "set":
                self.set(operation[key], operation[value])
                response = f"key {operation[key]} set to {operation[value]}"
            elif(operation[command] == "delete"):
                self.delete(operation[key])
                response = f"Key operation[key] was deleted!"
            elif(operation[command] == "show"):
                response = str(self.keyValueStore)
            else:
                pass

        return response

        
    # bring the key value store upto spec!
    def catch_up(self):
        if os.path.exists(self.server_name + "_log.txt"):
            f = open(self.server_name + "_log.txt", "r")
            log = f.read()
            f.close()

            for command in log.split('\n'):
                self.execute(command)
        