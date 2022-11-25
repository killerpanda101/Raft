import socket

# fixed size header to 
HEADERSIZE = 10

# append message header before sending
def Send(conn, msg):
    msg = f"{len(msg):<{HEADERSIZE}}"+msg
    conn.sendall(msg.encode('utf-8'))

# TO-DO handel failures!
# remove message header and send back response
def Recv(conn):

    while True:
        full_msg = ""
        new_msg = True

        while True:
            msg = conn.recv(HEADERSIZE+6)
            
            if new_msg:
                # get message length first
                msg_len = int(msg[:HEADERSIZE])
                new_msg = False

            full_msg += msg.decode("utf-8")

            if len(full_msg)-HEADERSIZE == msg_len:
                # full message recieved
                return full_msg[HEADERSIZE:]






