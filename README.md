# Raft Consensus Algorithm in Python

This project is an implementation of the Raft consensus algorithm in Python. Raft is used for managing a replicated log in a distributed system.

## Project Structure
```
Raft-main/
├── logs/                          # Log files for the severs part of the system.
│   ├── server_registry.txt        # Name and IP address of the servers in the cluster.
├── run_servers.sh                 # Shell script for running multiple server instances.
├── src/                         
│   ├── append_entries_call.py     # Contains the logic for the "AppendEntries" RPC call in Raft.
│   ├── client.py                  # Client-side code for the Raft implementation.
│   ├── config.py                  # Keeps track of the servers in the system.
│   ├── key_value_store.py         # key-value store implemented on top of Raft.
│   ├── log_data_access_object.py  # Handles access to log data.
│   ├── message_passing.py         # Contains helpers for socket communication.
│   ├── parsing.py                 # Contains utilities for sending messages between servers.
│   └── request_vote_call.py       # Contains the logic for the "RequestVote" RPC call in Raft.
├── startClient.py                 # Python script used for starting the Raft client.
└── startServer.py                 # Python script used for starting the Raft server.
```

## How to Run
  
-  The key-value store lets you use GET, SET, and DELETE commands to manage data.
-   Only the leader is responsible for handling these commands and updates the followers with any changes made by a client.
-   If the leader goes down, a new leader is automatically chosen from among the followers.
-   When a failed server is restarted, the leader ensures that its logs are updated to the current state.

### Step 1: Prepare Server Logs

1.  INavigate to the `Raft-main/logs` folder and create 5 text files, one for each server's logs:

    -   `server2_log.txt`
    -   `server3_log.txt`
    -   `server4_log.txt`
    -   `server5_log.txt`
    -   `server6_log.txt`
    
2.  Still in the `Raft-main/logs` folder, create a file named `server_registry.txt`. List the names, IP addresses, and port numbers of all servers as shown below:
	```
	server2 localhost 2000
	server3 localhost 3000
	server4 localhost 4000
	server5 localhost 5000
	server6 localhost 6000
	```    
3. When you run the code, each server's log file will be initialized with a basic log entry, serving as a starting point for all servers in the cluster.
    
    `0  0  set unreachable`
    
  > **Note:** This setup is essential because it informs each server about the other servers in the cluster. Without this information, each server would keep voting for itself as the leader.


### Step 2: Running the servers and the client

1. Launch the 5 servers using the command: `python startServer.py [server_name] [ip] [port] False`
	- You can automate this step by running the `run_server.sh` script, which opens 5 terminals and starts the servers.
	- After launching, the servers will hold an election to choose a leader.
	
2. To start the client, use the command:`python startClient.py [leader_ip] [leader_port]`
	- To execute this successfully, you'll need to know which server has become the leader. You can:
		- Check the server output to determine this, or
		-  Connect to any server and attempt a GET, SET, or DELETE command. If the connected server is not the leader, it will reply with the leader's IP address.
		
### Step 3: Log replication

1. Once everything is up and running, you can use the client to instruct the leader to carry out operations like this:
	```
	set [key] [value]
	get [key]
	delete [key]
	```	
	
	example:
	```
	set a 1
	get a
	delete a
	```
2. To test the leader election feature, shut down the current leader. A new leader will be automatically chosen from the remaining followers.
3. To test the recovery process for failed servers, erase the log entries for the server you took offline from the `Raft-main/logs` folder. When you restart the server:
	- It will rejoin the cluster as a follower, and
	- The new leader will update the follower's logs to the latest state.

