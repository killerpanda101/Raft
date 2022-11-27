import sys
from client import Client

if(len(sys.argv) != 2):
    print("Usage python startClient.py (server_port)")
    exit

Client(server_port=int(sys.argv[1])).start()