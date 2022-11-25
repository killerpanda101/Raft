import json
import threading

class KeyValueStore:
    client_lock = threading.Lock()

    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data[key]

    def set(self, key, value):
        self.data[key] = value

    def delete(self, key):
        del self.data[key]

    def execute(self, operationStr):
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