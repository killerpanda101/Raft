import os
import threading

from src.log_data_access_object import LogDataAccessObject


class KeyValueStore:
    LOG_DIR = "logs/"
    BASE_LOG_ENTRY = "0 0 set unreachable"
    CLIENT_LOCK = threading.Lock()

    def __init__(self, server_name):
        self.server_name = server_name
        self.data = {}
        self.log = []
        self.catch_up_successful = False
        self.current_term = 0
        self.latest_term_in_logs = 0 
        self.highest_index = 1
        self.log_recently_changed = False

    def _get_log_path(self):
        return f"{self.LOG_DIR}{self.server_name}_log.txt"

    # the three operations that the key value store supports
    def get(self, key):
        return self.data.get(key, "Key Does Not Exist!")

    def set(self, key, value):
        self.data[key] = value

    def delete(self, key):
        self.data.pop(key, None)

    # bring the key value store upto spec!
    def catch_up(self, path_to_logs='', new_leader=False):
        if path_to_logs == '':
            path_to_logs = "logs/" + self.server_name + "_log.txt"

        if os.path.exists(path_to_logs):
            with open(path_to_logs, "r+") as f:
                all_lines = f.read().splitlines()
                non_empty_lines = list(filter(lambda x: x != '', all_lines))

                # Ensure the first line is "0 0 set  unreachable" (base log)
                if len(non_empty_lines) == 0 or non_empty_lines[0] != "0 0 set  unreachable":
                    f.seek(0)
                    f.write("0 0 set  unreachable\n")
                    f.write('\n'.join(all_lines) + '\n')

                # Read the updated lines
                f.seek(0)
                all_lines = f.read().splitlines()

                last_command = ''
                for command in all_lines:
                    if command != '':
                        last_command = command
                        self.write_to_state_machine(command, term_absent=False)

                if last_command != '':
                    components = last_command.split(' ')

                    # increment the index from the last call
                    # so that the next log entry continues the count upward
                    self.highest_index = int(components[0])
                    self.latest_term_in_logs = int(components[1])

                if not new_leader:
                    self.current_term = self.latest_term_in_logs

            print("Latest term in logs: " + str(self.latest_term_in_logs))
            print("Current term: " + str(self.current_term))

        self.catch_up_successful = True
        self.log_recently_changed = True


    def remove_logs_after_index(self, index, path_to_logs=''):
        if path_to_logs == '':
            path_to_logs = "logs/" + self.server_name + "_log.txt"

        if os.path.exists(path_to_logs):
            f = open(path_to_logs, "r+")
            log_list = f.readlines()

            while '' in log_list:
                log_list.remove('')
            f.seek(0)
            for line_to_keep in log_list[0:index + 1]:
                f.write(line_to_keep)
            f.truncate()
            f.close()
            self.log_recently_changed = True

    def log_access_object(self, path_to_logs=''):
        if not self.log_recently_changed:
            pass
        else:
            dict_for_state_machine = {}
            array_for_index_terms = []
            if path_to_logs == '':
                path_to_logs = "logs/" + self.server_name + "_log.txt"

            if os.path.exists(path_to_logs):
                f = open(path_to_logs, "r")
                log = f.read()
                f.close()

                for command in log.split('\n'):
                    if command != '':
                        operands = command.split(" ")

                        dict_for_state_machine[" ".join(operands[:2])] = " ".join(operands)
                        array_for_index_terms.append(" ".join(operands[:2]))

            self.cached_log_access_object = LogDataAccessObject(array=array_for_index_terms, dict=dict_for_state_machine)
            self.log_recently_changed = False

        return self.cached_log_access_object

    def command_at(self, previous_index, previous_term):
        # get the command at "index term" combo.
        return self.log_access_object().term_indexed_logs. \
            get(str(previous_index) + " " + str(previous_term))

    def get_latest_term(self):
        if not self.catch_up_successful:
            print("This store isn't caught up, so it doesn't know what term we're in!")
            return

        return self.latest_term_in_logs

    def write_to_state_machine(self, string_operation, term_absent, path_to_logs=''):
        print("Writing to state machine: " + string_operation)

        if len(string_operation) == 0:
            return

        if term_absent:
            string_operation = str(self.highest_index) + " " + str(self.latest_term_in_logs) + " " + string_operation

        operands = string_operation.split(" ")
        index, term, command, key, values = 0, 1, 2, 3, 4

        response = "Sorry, I don't understand that command."

        with self.client_lock:
            self.latest_term_in_logs = int(operands[term])

            if operands[command] == "set":
                value = " ".join(operands[values:])

                self.log.append(string_operation)
                self.set(operands[key], value)
                response = f"key {operands[key]} set to {value}"
            elif operands[command] == "delete":
                self.log.append(string_operation)
                self.delete(operands[key])
                response = f"key {key} deleted"
            else:
                pass

        return response

    #  client operations that do not modify state (GET/SHOW)
    def read(self, string_operation):
        print(string_operation)

        if len(string_operation) == 0:
            return

        # get the client request to see what it wants
        operands = string_operation.split(" ")
        print("the read command is " + string_operation)
        command, key, values = 0, 1, 2

        # in case of invalid client command 
        response = "Sorry, I don't understand that command."

        # this is the client reads
        with self.client_lock:
            if operands[command] == "get":
                response = self.get(operands[key])
            # show returns everyting, use this to debug    
            elif operands[command] == "show":
                response = str(self.data)
            else:
                pass

        return response

    def write_to_log(self, string_operation, term_absent, path_to_logs=''):
        print("Writing to log: " + string_operation)
        self.log_recently_changed = True

        if len(string_operation) == 0:
            return ''

        operands = string_operation.split(" ")

        if term_absent or len(operands) in (2, 3):
            command, key, values = 0, 1, 2
        else:
            index, term, command, key, values = 0, 1, 2, 3, 4

        if operands[command] in ["set", "delete"]:
            if term_absent or len(operands) in (2, 3):
                self.highest_index += 1
                string_operation = str(self.highest_index) + " " + str(self.current_term) + " " + string_operation
            else:
                self.highest_index = index + 1
                self.latest_term_in_logs = term

            if path_to_logs == '':
                path_to_logs = "logs/" + self.server_name + "_log.txt"
            f = open(path_to_logs, "a+")
            f.write(string_operation + '\n')
            f.close()

            self.latest_term_in_logs = self.current_term

            return string_operation

        return ''
