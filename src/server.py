import ast
from socket import *
import threading
import time
import random


from src.append_entries_call import AppendEntriesCall
from src.request_vote_call import RequestVoteCall
from src.config import other_server_names
from src.key_value_store import KeyValueStore
from src.message_passing import receive_message, send_message
from src.parsing import with_return_address, broadcast, return_address_and_message, address_of


class Server:
    def __init__(self, name, ip, port=10000, leader=False):
        self.port = port
        self.name = name
        self.key_value_store = KeyValueStore(server_name=name)
        self.key_value_store.catch_up()
        self.latest_leader = "yet unelected"

        self.leader = leader
        self.heartbeat_timer = None
        self.followers_with_update_status = {}
        self.current_operation = ''
        self.current_operation_committed = False
        self.ip = ip

        self.timeout = float(random.randint(10, 18))
        self.election_countdown = threading.Timer(self.timeout, self.start_election)
        print("Server started with timeout of : " + str(self.timeout))
        self.election_countdown.start()
        self.voted_for_me = {}

        for server_name in other_server_names(name):
            self.followers_with_update_status[server_name] = False

        for server_name in other_server_names(name):
            self.voted_for_me[server_name] = False
        self.voted_for_me[self.name] = False

    def start_election(self):
        if not self.leader:
            self.key_value_store.current_term += 1

            # restart election if no leader is successfully elected.
            self.timeout = float(random.randint(10, 18))
            self.election_countdown = threading.Timer(self.timeout, self.start_election)
            print("Server reset election timeout to : " + str(self.timeout))
            self.election_countdown.start()

            self.voted_for_me[self.name] = True
            broadcast(self, with_return_address(
                self,
                RequestVoteCall(
                    for_term=str(self.key_value_store.current_term),
                    latest_log_index=str(self.key_value_store.highest_index),
                    latest_log_term=str(self.key_value_store.latest_term_in_logs)
                ).to_message()
                ))

    def send(self, message, to_server_address):
        print(f"connecting to {to_server_address[0]} port {to_server_address[1]}")

        peer_socket = socket(AF_INET, SOCK_STREAM)

        try:
            peer_socket.connect(to_server_address)
            encoded_message = message.encode('utf-8')
            try:
                print(f"sending {encoded_message} to {to_server_address}")
                send_message(peer_socket, encoded_message)
                time.sleep(1)
                peer_socket.close() 
            except Exception as e:
                print(f"closing socket due to {str(e)}")
                peer_socket.close()
        except OSError as e:
            print("Bad file descriptor: " + str(e))
        except ConnectionRefusedError as e:
            print(f"Oops, looks like {to_server_address[0]} port {to_server_address[1]} isn't up right now")

    # setting up a listening socket!
    def start(self):
        server_address = (self.ip, self.port)

        print("starting up on " + str(server_address[0]) + " port " + str(server_address[1]))
        
        # socket config
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_socket.bind(server_address)
        self.server_socket.listen(6000)

        if self.leader:
            self.prove_aliveness()

        while True:
            # accept new connection and spawn thread
            connection, client_address = self.server_socket.accept()
            print(f"connection from {client_address}")
            threading.Thread(target=self.manage_messaging, args=(connection, self.key_value_store)).start()

    def prove_aliveness(self):
        print("Sending Heartbeat!")
        if self.leader:
            broadcast(self, with_return_address(
                self,
                AppendEntriesCall(
                    in_term=self.key_value_store.current_term,
                    previous_index=self.key_value_store.highest_index,
                    previous_term=self.key_value_store.latest_term_in_logs,
                    entries=[]
                ).to_message()
            ))
            self.heartbeat_timer = threading.Timer(5.0, self.prove_aliveness)
            self.heartbeat_timer.start()

    # this function is key, it checks to see if quorum is reached or not!
    # runs every time a follwer responds with append entries successfull.
    def mark_updated(self, server_name):
        self.followers_with_update_status[server_name] = True

        trues = len(list(filter(lambda x: x is True, self.followers_with_update_status.values())))
        falses = len(list(filter(lambda x: x is False, self.followers_with_update_status.values())))
        if trues >= falses:
            print("Committing entry: " + self.current_operation)
            self.current_operation_committed = True
            self.key_value_store.write_to_state_machine(self.current_operation, term_absent=True)
            broadcast(self, with_return_address(self, "commit_entries ['" + self.current_operation + "']"))

            self.current_operation_committed = False
            for server_name in other_server_names(self.name):
                self.followers_with_update_status[server_name] = False

    def mark_voted(self, server_name):
        self.voted_for_me[server_name] = True

        trues = len(list(filter(lambda x: x is True, self.voted_for_me.values())))
        falses = len(list(filter(lambda x: x is False, self.voted_for_me.values())))
        if trues >= falses:
            print("I win the election for term " + str(self.key_value_store.current_term) + "!")
            self.key_value_store.catch_up(new_leader=True)
            self.leader = True

            self.prove_aliveness()

            for server_name in other_server_names(self.name):
                self.voted_for_me[server_name] = False
            self.voted_for_me[self.name] = False

    # once the socket connection is established
    def manage_messaging(self, connection, kvs):
        try:
            while True:
                # get the data
                operation = receive_message(connection)

                # perform the opp
                if operation:
                    destination, response = self.respond(kvs, operation)

                    if response == '':
                        break

                    # send the data back
                    if destination == "client":
                        send_message(connection, response.encode('utf-8'))
                    else:
                        self.send(response, to_server_address=address_of(destination))

                else:
                    break

        finally:
            connection.close()

    def respond(self, key_value_store, operation):
        send_pending = True
        string_request = operation.decode("utf-8")
        server_name, string_operation = return_address_and_message(string_request)
        print("from " + server_name + ": received " + string_operation)

        response = ''

        # follower workflow if the request is intended for the follower!
        if string_operation.split(" ")[0] == "append_entries":
            call = AppendEntriesCall.from_message(string_operation)

            # term checking
            if call.in_term < self.key_value_store.current_term:
                response = "Your term is out of date. You can't be the leader."
            else:
                # The storing the last server that reached out in a leaderly fashion.
                self.latest_leader = server_name
                
                # reset timer
                self.election_countdown.cancel()
                self.election_countdown = threading.Timer(self.timeout, self.start_election)
                self.election_countdown.start()

                self.leader = False
                if self.heartbeat_timer:
                    self.heartbeat_timer.cancel()
                self.key_value_store.current_term = call.in_term

                # update logs
                if self.key_value_store.command_at(
                    call.previous_index,
                    call.previous_term
                ) != None:
                    key_value_store.remove_logs_after_index(call.previous_index)
                    [key_value_store.write_to_log(log, term_absent=False) for log in call.entries]
                    print("State machine after appending: " + str(key_value_store.data))

                    response = "Append entries call successful!"
                else:
                    response = "append_entries_unsuccessful. Please send log prior to: " + str(call.previous_index) + " " + str(call.previous_term)

        # send one older entry! (follower catchup)
        elif string_operation.split(" ")[0] == "append_entries_unsuccessful.":

            response_components = string_operation.split(" ")
            max_index = len(response_components)

            latest_tried_index = int(response_components[max_index - 2])
            latest_tried_term = int(response_components[max_index - 1])

            log_position = self.key_value_store.log_access_object().ordered_logs.index(
                str(latest_tried_index) + " " + str(latest_tried_term)
            )

            ordered_logs = self.key_value_store.log_access_object().ordered_logs
            term_indexed_logs = self.key_value_store.log_access_object().term_indexed_logs
            new_key_to_try = ordered_logs[log_position - 1]

            new_values_to_send = list(
                map(
                    lambda x: term_indexed_logs[x],
                    ordered_logs[log_position:]
                )
            )

            try_this_index = new_key_to_try.split(" ")[0]
            try_this_term = new_key_to_try.split(" ")[1]

            response = AppendEntriesCall(
                in_term=self.key_value_store.current_term,
                previous_index=try_this_index,
                previous_term=try_this_term,
                entries=new_values_to_send
            ).to_message()

        # branch that commits follower entries once quorum is reached!
        elif string_operation.split(" ")[0] == "commit_entries":
            stringified_logs_to_append = string_operation.replace("commit_entries ", "")
            print("Preparing to commit: " + stringified_logs_to_append)
            logs_to_append = ast.literal_eval(stringified_logs_to_append)
            [key_value_store.write_to_state_machine(command, term_absent=True) for command in logs_to_append]

            response = "Commit entries call successful!"
            print("State machine after committing: " + str(key_value_store.data))

        # messages that do not need any responses!
        elif string_operation in [
            "Caught up. Thanks!",
            "Sorry, I don't understand that command.",
            "Broadcasting to other servers to catch up their logs.",
            "Commit entries call successful!",
            "Sorry, already voted.",
            "Your term is out of date. You can't be the leader.",
            "Your log is out of date. I'm not voting for you!"
        ] or string_operation.startswith("I am not the leader"):
            send_pending = False

        elif string_operation.split(" ")[0] == "can_I_count_on_your_vote_in_term":
            request_vote_call = RequestVoteCall.from_message(string_operation)
            if request_vote_call.for_term > self.key_value_store.current_term \
                and request_vote_call.latest_log_term >= self.key_value_store.latest_term_in_logs \
                and request_vote_call.latest_log_index >= self.key_value_store.highest_index:
                    response = "You can count on my vote!"
            else:
                response = "Your log is out of date. I'm not voting for you!"

        elif string_operation == "You can count on my vote!":
            self.mark_voted(server_name)
            self.key_value_store.current_term += 1
            send_pending = False

        elif string_operation == "Append entries call successful!":
            if self.leader:
                self.mark_updated(server_name)
            send_pending = False

        # Interactions between the leader and client 
        else:
            if self.leader:
                self.current_operation = string_operation

                if self.current_operation.split(" ")[0] in ["set", "delete"]:
                    string_operation_with_term = key_value_store.write_to_log(string_operation, term_absent=True)
                    broadcast(self, with_return_address(
                        self,
                        AppendEntriesCall(
                            in_term=self.key_value_store.current_term,
                            previous_index=self.key_value_store.highest_index - 1,
                            previous_term=self.key_value_store.latest_term_in_logs,
                            entries=[string_operation_with_term]
                        ).to_message()
                    ))

                    # waiting till we get quorum!
                    #TODO: Something about this block closes the connection
                    while not self.current_operation_committed:
                        pass
                        # self.current_operation_committed = False

                    response = "Success!"

                else:
                    response = key_value_store.read(self.current_operation)
            else:
                response = "I am not the leader. The last leader I heard from is: " + str(self.latest_leader)

        if send_pending:
            response = with_return_address(self, response)

        return server_name, response
