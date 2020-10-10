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
import select
import traceback
sys.path.append("..")

# Custom imports
from helper import Logger
from helper import Messenger
from ports  import ports
from ports  import HOST

MY_NAME = "" #Determined at runtime.

MAX_MSG_LEN = 1024 #Max number of bytes we're willing to receive at once.

SERVE_CLIENT_PERIOD = 0.01 #seconds

# # # # # # # # # # # # #
# THREAD FUNCTION DEFNS #
# # # # # # # # # # # # #
# Function to serve a single client.
def serve_clients():
    # Ensure that we are referencing the global num_enemies
    global num_enemies
    global clients_lock

    logger = Logger()
    messenger = Messenger(None, '', '', logger)

    try: 
        while(1):

            while(not clients):
                pass

            #Give the main loop time to get more clients.
            time.sleep(SERVE_CLIENT_PERIOD)

            clients_lock.acquire()
            readable,writable,exceptional = select.select(clients,[],[],0)

            for conn in readable:

                # Get the message from the client.
                msg = messenger.recv(conn)

                if msg:
                    try: 
                        attack = int(msg.split(')')[1])
                        req_num = int(msg.split(')')[0].split('#')[1])
                    except (IndexError, ValueError) as e:
                        logger.error('Bad message from client.')
                        continue
                else:
                    continue

                # x represents the number of enemies killed.
                logger.info(f"Before Request: S={num_enemies}")
                num_enemies = num_enemies - attack
                logger.info(f"After Request: S={num_enemies}")

                messenger.socket = conn
                messenger.send(f"(Req#{req_num}){num_enemies} FORMICS REMAIN")

            clients_lock.release()
    except Exception as e:
        traceback.print_exc()
        #If something happens to the client-serving part of the server,
        #everything should die.
        thread.interrupt_main()
        return

# Function to receive heartbeats and reply to them.
def serve_LFD(hb_conn, addr):
    #with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as r_socket:

    messenger = Messenger(hb_conn, 'S1', '')
                
    try:
        while(1):
            # Wait for the client to send a heartbeat and echo it back.
            msg = messenger.recv(hb_conn)
            if msg:
                messenger.send(msg)     

    except KeyboardInterrupt:
        print("Killing heartbeat thread.")
        exit()


def main():
    # Open the top-level listening socket.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        #Set the socket address so it can be reused without a timeout.
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind to the network port specified at top.
        s.bind((HOST, ports[f"{MY_NAME}_LISTEN"]))

        # This should be a listening port.
        s.listen()

        # Flavor Text
        print("\n'From now on the enemy is more clever than you.")
        print(" From now on the enemy is stronger than you.")
        print(" From now on you are always about to lose.'\n")

        print("<<< WELCOME, COMMANDER >>>")
        print("\nAnd remember, this is just a game.")
        print(num_enemies, "FORMICS REMAIN")

        server = threading.Thread(target=serve_clients, args=(), daemon=True)
        server.start();
        
        #Run forever
        try:
            while True:
            
                # Wait (blocking) for connections.
                conn, addr = s.accept()

                clients_lock.acquire()
                clients.append(conn)
                clients_lock.release()
        except Exception as e: 
            traceback.print_exc()
            s.shutdown()
            s.close() #Gracefully exit by closing s & all connections.
            for conn in clients:
                conn.shutdown()
                conn.close()
            return



        
if __name__ == '__main__':

    # Parse replica number from CLI
    if len(sys.argv) < 2:
        raise ValueError("No Replica Number Provided!")

    if len(sys.argv) > 2:
        raise ValueError("Too Many CLI Arguments!")

    replica_num = int(sys.argv[1])

    MY_NAME = "S" + str(replica_num)

    # Global variable num_enemies holds the number of enemies remaining.
    # This starts at 1000 and can be decremented by clients.
    num_enemies = 1000

    # Protect this shared variable with a lock to prevent race conditions.
    #num_enemies_lock = threading.Lock()

    clients = []

    clients_lock = threading.Lock()

    print(f"{MY_NAME} Waiting for LFD...")
    
    # Before we do anything, make sure the heartbeat is working.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        #Set the socket address so it can be reused without a timeout.
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Create the heartbeat port.
        s.bind((HOST, ports[f"{MY_NAME}_HB"]))

        # This should be a listening port.
        s.listen()

        # Get the HEARTBEAT connection.
        conn, addr = s.accept()

        #Kick off the LFD-server connection.
        print("Connection with LFD established!")

        #Make the heartbeat thread a daemon thread so it dies if the rest of
        #the program goes down.
        heartbeat = threading.Thread(target=serve_LFD, args = (conn,addr), daemon=True)
        heartbeat.start()

    main()
