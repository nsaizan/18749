#
#    File: Server Application
#  Author: aquinn, nsaizan, ranz2
#   Group: TheEnemy'sGateIsDown
#    Date: 9/14/2020
#
# Main code for our server.

# Standard imports
import socket
import threading
import sys
import time
sys.path.append("..")

# Custom imports
from helper import Logger
from helper import Messenger

# # # # # # # # # # # # #
# HOST & PORT SETTINGS  #
# # # # # # # # # # # # #

HOST = ''    #Accept connections on any IPv4 interface
PORT = 36337

LFD_HOST = '127.0.0.1' # Local Fault Detector should be on this machine.
LFD_PORT = 36338

HEARTBEAT_FREQ_DEFAULT = 3 # Frequency in Hz


# # # # # # # # # # # # #
# THREAD FUNCTION DEFNS #
# # # # # # # # # # # # #
# Function to serve a single client.
def serve_client(conn, addr):
    # Ensure that we are referencing the global num_enemies
    global num_enemies
    global num_enemies_lock

    logger = Logger()
    messenger = Messenger(None, '', '', logger)

    while(1):
        # Wait for the client to send a single byte.
        msg = messenger.recv(conn, 9)

        if msg: 
            attack = int(msg)
        else:
            continue

        # x represents the number of enemies killed. 
        num_enemies_lock.acquire()
        num_enemies = num_enemies - attack
        logger.info(f"{num_enemies} FORMICS REMAIN")
        num_enemies_lock.release()


# Function to send out a heartbeat repeatedly at a given frequency.
def send_heartbeat():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as heartbeat_socket:
        logger = Logger()

        try:
            # Keep trying to connect to LFD til it is successful
            while(heartbeat_socket.connect_ex((LFD_HOST, LFD_PORT)) != 0):
                logger.info("Please start the LFD")
                time.sleep(1)

            messenger = Messenger(heartbeat_socket, 'S1', 'LFD1', logger)
            messenger.info("Successfully Connected to LFD")

            # TODO
            # Now just send heartbeat to local detector, should send through each
            # replicated server later on
            count = 0

            while True:
                # Create unique message from source and a counter
                msg = f"{PORT}{format(count, '05d')}"
                count += 1

                # Send and log the message
                messenger.send(msg)

                # Handle frequency
                time.sleep(1/int(HEARTBEAT_FREQ_DEFAULT))

        except KeyboardInterrupt:
            print("Killing heartbeat thread.")
            exit()

def main():
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

if __name__ == '__main__':
    # Parse heartbeat frequency from the CLI
    if len(sys.argv) < 2:
        freq = HEARTBEAT_FREQ_DEFAULT
        print(f"Using the Default Heartbeat Frequency: {HEARTBEAT_FREQ_DEFAULT}")
    else:
        raise ValueError("Too Many CLI Arguments!")

    # Global variable num_enemies holds the number of enemies remaining.
    # This starts at 1000 and can be decremented by clients.
    num_enemies = 1000

    # Protect this shared variable with a lock to prevent race conditions.
    num_enemies_lock = threading.Lock()

    # Initialize heartbeat.
    heartbeat = threading.Thread(target=send_heartbeat, args = ())
    heartbeat.start()

    main()
