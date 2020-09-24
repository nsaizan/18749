#
#    File: Server Application
#  Author: aquinn, nsaizan, ranz2
#   Group: TheEnemy'sGateIsDown
#    Date: 9/14/2020
#
# Main code for our server.

import socket
import threading
import sys
import time

# # # # # # # # # # # # #
# HOST & PORT SETTINGS  #
# # # # # # # # # # # # #

HOST = ''    #Accept connections on any IPv4 interface
PORT = 36337

LFD_HOST = '127.0.0.1' # Local Fault Detector should be on this machine.
LFD_PORT = 36338


# # # # # # # # # # # # #
# THREAD FUNCTION DEFNS #
# # # # # # # # # # # # #
# Function to serve a single client.
def serve_client(conn, addr):
    # Ensure that we are referencing the global num_enemies
    global num_enemies
    global num_enemies_lock

    while(1):
        # Wait for the client to send a single byte.
        x = conn.recv(1)
        if(x == b''):
            print(f"INFO: Client {addr} closed connection")
            break
        x = int(x)

        # x represents the number of enemies killed. 
        num_enemies_lock.acquire()
        num_enemies = num_enemies - x
        print(num_enemies, " FORMICS REMAIN")
        num_enemies_lock.release()


# Function to send out a heartbeat repeatedly at a given frequency.
def send_heartbeat(frequency):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as heartbeat_socket:
        # Connect to the detector
        try:
            heartbeat_socket.connect((LFD_HOST, LFD_PORT))

            # TODO
            # Now just send heartbeat to local detector, should send through each
            # replicated server later on

            msg = str(PORT)
            heartbeat_msg = msg.encode()

            while True:
                heartbeat_socket.send(heartbeat_msg)
                time.sleep(int(frequency))
        except Exception as e:
            print("Please launch the local machine to test fault detector module.")


# # # # # # # # #
# STARTUP CODE  #
# # # # # # # # #

# Parse heartbeat frequency from the CLI
if len(sys.argv) < 2:
    raise ValueError("No Heartbeat Frequency Provided!")

if len(sys.argv) > 2:
    raise ValueError("Too Many CLI Arguments!")

freq = sys.argv[1]

# Global variable num_enemies holds the number of enemies remaining.
# This starts at 1000 and can be decremented by clients.
num_enemies = 1000

# Protect this shared variable with a lock to prevent race conditions.
num_enemies_lock = threading.Lock()

# Initialize heartbeat.
heartbeat = threading.Thread(target=send_heartbeat, args = (freq,))
heartbeat.start()

# # # # # 
# MAIN  #
# # # # #
# Open the top-level listening socket.
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

    # Bind to the network port specified at top.
    s.bind((HOST, PORT))

    # This should be a listening port.
    s.listen()

    # Flavor Text
    print("\n'From now on the enemy is more clever than you.")
    print(" From now on the enemy is stronger than you.")
    print(" From now on you are always about to lose.'\n")

    print("<<< WELCOME, COMMANDER >>>")
    print("\nAnd remember, this is just a game.")
    print(num_enemies, "FORMICS REMAIN")
    #Run forever
    while True:
        
        # Wait (blocking) for connections.
        conn, addr = s.accept()

        # Start a new thread to service the client.
        server = threading.Thread(target=serve_client, args=(conn,addr))

        server.start()
