import sys

from src.client import Client

Client(ip=str(sys.argv[1]), server_port=int(sys.argv[2])).start()
