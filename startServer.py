import sys

from src.server import Server

am_i_the_leader = False
if len(sys.argv) > 4 and sys.argv[4] == 'True':
    am_i_the_leader = True

Server(name=str(sys.argv[1]), ip=str(sys.argv[2]), port=int(sys.argv[3]), leader=am_i_the_leader).start()