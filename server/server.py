#
#    File: Server Application
#  Author: aquinn, nsaizan, ranz2
#   Group: TheEnemy'sGateIsDown
#    Date: 9/14/2020
#
# Main code for our server.

# Standard imports
import socket
import _thread
import threading
import sys
import time
import select
import traceback
import random
sys.path.append("..")

# Custom imports
from helper import Logger
from helper import Messenger
from ports  import ports
from ports  import HOST
from ports  import ACTIVE_REPLICATION

MY_NAME = "" # Determined at runtime.
BACKUP1_NAME = ""
BACKUP2_NAME = ""

MAX_MSG_LEN = 1024 # Max number of bytes we're willing to receive at once.

SERVE_CLIENT_PERIOD = 0.01 # seconds

SEND_CP_PERIOD = 5 # seconds

cp_num = 0 # Checkpoint number
last_cp_time = None # Last time we sent a checkpoint

backup1, backup2 = None, None
backup1_alive, backup2_alive = False, False
backup1_messenger, backup2_messenger = None, None

# Active Replication Quiescense Flag
WE_ARE_READY = False

# Passive Replication Primary Flag
WE_ARE_PRIMARY = False


# # # # # # # # # # # # #
# THREAD FUNCTION DEFNS #
# # # # # # # # # # # # #

def wait_for_clients():
    while(not clients):
        pass

def parse_client_message(logger, msg):
    attack = None
    req_num = None
    ret_val = False

    if msg:
        if "Req" in msg:
            try: 
                attack = int(msg.split(')')[1])
                req_num = int(msg.split(')')[0].split('#')[1])
                ret_val = True
            except (IndexError, ValueError):
                logger.error('Bad message from client.')

    return attack, req_num, ret_val

def parse_checkpoint_message(logger, msg):
    state = None
    cp_num = None
    ret_val = False

    if msg:
        if "Checkpoint" in msg:
            try: 
                state = int(msg.split(')')[1])
                cp_num = int(msg.split(')')[0].split('#')[1])
                ret_val = True
            except (IndexError, ValueError):
                logger.error('Bad checkpoint message!')

    return state, cp_num, ret_val

def parse_primary_assignment_message(logger, msg):
    ret_val = False
    
    if msg:
        if "Primary" in msg:
            ret_val = True

    return ret_val

def parse_send_checkpoint_message(logger, msg):
    ret_val = False

    if msg:
        if "Send Checkpoint" in msg:
            ret_val = True

    return ret_val

def parse_set_ready_message(logger, msg):
    ret_val = False

    if msg:
        if "Ready" in msg:
            ret_val

    return ret_val

def repair_connection(logger, port_name, destination):
    new_server = None
    new_status = False
    new_messenger = None
    try:
        new_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        new_server.connect((HOST, ports[port_name]))
        new_messenger = Messenger(new_server, MY_NAME, destination, logger)
        new_status = True
    except Exception:
        new_status = False

    return new_server, new_status, new_messenger

def repair_connections(logger, backups, statuses, messengers):
    if statuses[0] == False:
        new_connection = repair_connection(logger, f"{BACKUP1_NAME}_LISTEN", BACKUP1_NAME)
        backups[0], statuses[0], messengers[0] = new_connection

    if statuses[1] == False:
        new_connection = repair_connection(logger, f"{BACKUP2_NAME}_LISTEN", BACKUP2_NAME)
        backups[1], statuses[1], messengers[1] = new_connection

    return backups, statuses, messengers

def its_time_to_send_cp():
    global last_cp_time

    current_time = time.time()

    if last_cp_time == None:
        last_cp_time = current_time
        return True

    if (current_time - last_cp_time) > SEND_CP_PERIOD:
        last_cp_time = current_time
        return True

    return False

def send_checkpoint(logger, num_enemies):
    global backup1, backup2
    global backup1_alive, backup2_alive
    global backup1_messenger, backup2_messenger

    global cp_num

    # Ensure we are the primary replica
    if not WE_ARE_PRIMARY:
        return

    # Repair connections if needed
    backups = [backup1, backup2]
    statuses = [backup1_alive, backup2_alive]
    messengers = [backup1_messenger, backup2_messenger]

    val = repair_connections(logger, backups, statuses, messengers)
    backups, statuses, messengers = val

    backup1, backup2 = backups
    backup1_alive, backup2_alive = statuses
    backup1_messenger, backup2_messenger = messengers

    if backup1_alive:
        try:
            backup1_messenger.send(f"(Checkpoint#{cp_num}) {num_enemies}")
        except Exception:
            backup1_alive = False
    if backup2_alive:
        try:
            backup2_messenger.send(f"(Checkpoint#{cp_num}) {num_enemies}")
        except Exception:
            backup2_alive = False

    cp_num += 1
    logger.info(f"Incrementing checkpoint count to {cp_num}")

# Function to serve a single client.
def serve_clients_and_replicas():
    # Ensure that we are referencing the global num_enemies
    global num_enemies
    global clients_lock
    global cp_num

    force_send_cp = False

    logger = Logger()
    messenger = Messenger(None, '', '', logger)

    try: 
        while(1):

            wait_for_clients()

            #Give the main loop time to get more clients.
            time.sleep(SERVE_CLIENT_PERIOD)

            clients_lock.acquire()

            readable = select.select(clients,[],[],0)[0]

            for conn in readable:
                # Get the message from the client.
                msg = messenger.recv(conn)

                # Parse checkpoints
                state, cp_num_new, is_cp = parse_checkpoint_message(logger, msg)

                # Parse client messages
                attack, req_num, is_client_msg = parse_client_message(logger, msg)

                # Parse primary assignment messages
                is_primary_assignment_msg = parse_primary_assignment_message(logger, msg)

                # Parse send checkpoint messages
                is_send_cp_msg = parse_send_checkpoint_message(logger, msg)

                # Parse set ready messages
                is_set_ready_msg = parse_set_ready_message(logger, msg)

                # Process checkpoints
                if is_cp:
                    # Process the checkpoint
                    logger.info(f"Updating internal state to: {state}")
                    num_enemies = state
                    logger.info(f"Updating checkpoint count to: {cp_num_new}")
                    cp_num = cp_num_new
                    WE_ARE_READY = True

                # Process client messages
                if is_client_msg and (WE_ARE_PRIMARY or (ACTIVE_REPLICATION and WE_ARE_READY)):
                    # Process the attack
                    logger.info(f"Before Request: S={num_enemies}")
                    num_enemies = num_enemies - attack
                    logger.info(f"After Request: S={num_enemies}")

                    # Respond to the attack
                    messenger.socket = conn
                    messenger.send(f"(Req#{req_num}){num_enemies} FORMICS REMAIN")

                # Process primary assignment messages
                if is_primary_assignment_msg:
                    logger.info(f"Updating Replica Status to Primary")
                    WE_ARE_PRIMARY = True

                # Process send checkpoint messages
                if is_send_cp_msg:
                    logger.info(f"Force Sending Checkpoint")
                    force_send_cp = True

                # Process set ready messages
                if is_set_ready_msg:
                    logger.info(f"Setting Ready Flag to True")
                    WE_ARE_READY = True

            # Send a checkpoint to backups
            # NOTE THAT this is outside the above for loop, so we are in a
            # quiescent state before sending the checkpoint. 
            if (not ACTIVE_REPLICATION and its_time_to_send_cp()) or force_send_cp:
                send_checkpoint(logger, num_enemies)
                
                force_send_cp = False

            clients_lock.release()

    except Exception:
        traceback.print_exc()
        #If something happens to the client-serving part of the server,
        #everything should die.
        _thread.interrupt_main()
        return

# Function to receive heartbeats and reply to them.
def serve_LFD(hb_conn, addr):

    messenger = Messenger(hb_conn, MY_NAME, '')
                
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

        server = threading.Thread(target=serve_clients_and_replicas, args=(), daemon=True)
        server.start()
        
        # Run forever
        try:
            while True:
                # Wait (blocking) for connections.
                conn = s.accept()[0]

                clients_lock.acquire()
                clients.append(conn)
                clients_lock.release()
        except Exception:
            # Gracefully exit by closing s & all connections.
            traceback.print_exc()
            s.close()
            for conn in clients:
                conn.close()
            return



        
if __name__ == '__main__':

    # Parse replica number from CLI
    if len(sys.argv) < 2:
        raise ValueError("No Replica Number Provided!")

    if len(sys.argv) > 2:
        raise ValueError("Too Many CLI Arguments!")

    replica_num = int(sys.argv[1])

    server_numbers = [1,2,3]
    MY_NAME = "S" + str(replica_num)

    server_numbers.remove(replica_num)
    BACKUP1_NAME = "S" + str(min(server_numbers))
    BACKUP2_NAME = "S" + str(max(server_numbers))

    # Global variable num_enemies holds the number of enemies remaining.
    # This starts at 1000 and can be decremented by clients.
    num_enemies = 1000

    clients = []

    clients_lock = threading.Lock()

    print(f"{MY_NAME} Waiting for LFD...")
    
    # Before we do anything, make sure the heartbeat is working.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        # Set the socket address so it can be reused without a timeout.
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Create the heartbeat port.
        s.bind((HOST, ports[f"{MY_NAME}_HB"]))

        # This should be a listening port.
        s.listen()

        # Get the HEARTBEAT connection.
        conn, addr = s.accept()

        # Kick off the LFD-server connection.
        print("Connection with LFD established!")

        # Make the heartbeat thread a daemon thread so it dies if the rest of
        # the program goes down.
        heartbeat = threading.Thread(target=serve_LFD, args = (conn,addr), daemon=True)
        heartbeat.start()

    main()
