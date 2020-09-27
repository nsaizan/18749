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
LFD_HB_PORT = 36338 # Port for Heartbeat (LFD->S)
LFD_R_PORT  = 36339 # Port for receipt   (S->LFD)

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


# Function to receive heartbeats and reply to them.
def serve_LFD(hb_conn, addr):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as r_socket:

        #Attempt to connect to the RECEIPT port.
        while(r_socket.connect_ex((LFD_HOST, LFD_R_PORT))):
            print("LFD Receipt Port Unavailable")
            time.sleep(1);
                
        try:
            while(1):
                # Wait for the client to send a 1-byte heartbeat. (Doesn't
                # matter what it is)
                msg = hb_conn.recv(1)
                if msg:
                    receipt = "HB received by server".encode()
                    r_socket.send(receipt)     
                
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

            # SEQUENTIALLY serve a new client.
            serve_client(conn,addr)
            #server = threading.Thread(target=serve_client, args=(conn,addr))

            server.start()

if __name__ == '__main__':

    # Global variable num_enemies holds the number of enemies remaining.
    # This starts at 1000 and can be decremented by clients.
    num_enemies = 1000

    # Protect this shared variable with a lock to prevent race conditions.
    num_enemies_lock = threading.Lock()

    print("Waiting for LFD...")
    # Before we do anything, make sure the heartbeat is working.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        # Create the heartbeat port.
        s.bind((LFD_HOST, LFD_HB_PORT))

        # This should be a listening port.
        s.listen()

        # Get the HEARTBEAT connection.
        conn, addr = s.accept()

        #Kick off the LFD-server connection.
        print("Connection with LFD established!")
        heartbeat = threading.Thread(target=serve_LFD, args = (conn,addr))
        heartbeat.start()

    main()
