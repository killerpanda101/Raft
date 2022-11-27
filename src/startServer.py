import sys
from server import Server

if(len(sys.argv) != 3):
    print("Usage python startServer.py (server_name) (port)")
    exit

Server(name=str(sys.argv[1]), port=int(sys.argv[2])).start()