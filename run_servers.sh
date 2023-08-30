#!/bin/bash

# Function to run a command in a new Terminal window
run_in_new_terminal() {
    osascript <<END
    tell application "Terminal"
        activate
        do script "cd $PWD && $1"
    end tell
END
}

# Array of server commands
server_commands=(
    "python3 startServer.py server2 localhost 2000 False"
    "python3 startServer.py server3 localhost 3000 False"
    "python3 startServer.py server4 localhost 4000 False"
    "python3 startServer.py server5 localhost 5000 False"
    "python3 startServer.py server6 localhost 6000 False"
)

# Run your server commands in new Terminal windows
for cmd in "${server_commands[@]}"; do
    run_in_new_terminal "$cmd"
done

# Exit the script in the currently running terminal
exit


