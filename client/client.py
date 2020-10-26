#
#    File: Client Application
#  Author: aquinn, nsaizan, ranz2
#   Group: TheEnemy'sGateIsDown
#    Date: 10/26/2020
#
# Main code for our client.

import socket
import time
import sys
import threading
sys.path.append("..")

# Custom imports
from helper import Logger
from helper import Messenger
from ports  import HOST
from ports  import ports

# # # # # # # # # # # # #
# HOST & PORT SETTINGS  #
# # # # # # # # # # # # #

# # # # # # # # # # # # #
# # GLOBAL VARIABLES  # #
# # # # # # # # # # # # #
to_be_receive = []
request_num = 0

s1, s2, s3 = None, None, None
s1_alive, s2_alive, s3_alive = False, False, False
s1_messenger, s2_messenger, s3_messenger = None, None, None

def listen2server(s_alive, messenger, s):
    if s_alive:
        try:
            msg = messenger.recv(s)
            if msg:
                try:
                    req_num = int(msg.split(')')[0].split('#')[1])
                except (IndexError, ValueError):
                    logger.error('Bad message from server.')
                if req_num in to_be_receive:
                    to_be_receive.remove(req_num)
                else:
                    logger.warning(" Discard duplicated info.")
        except Exception:
            s_alive = 0

def repair_connection(port_name, destination, client_num):
    new_server = None
    new_status = False
    new_messenger = None
    try:
        new_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        new_server.connect((HOST, ports[port_name]))
        new_messenger = Messenger(new_server, f'C{client_num}', destination, logger)
        new_status = 1
    except Exception:
        new_status = 0

    return new_server, new_status, new_messenger

def repair_connections(servers, statuses, messengers):
    global client_num

    if statuses[0] == 0:
        new_connection = repair_connection(f"S1_LISTEN", "S1", client_num)
        servers[0], statuses[0], messengers[0] = new_connection

    if statuses[1] == 0:
        new_connection = repair_connection(f"S2_LISTEN", "S2", client_num)
        servers[1], statuses[1], messengers[1] = new_connection

    if statuses[2] == 0:
        new_connection = repair_connection(f"S3_LISTEN", "S3", client_num)
        servers[2], statuses[2], messengers[2] = new_connection

    return servers, statuses, messengers

def main():
    # Run until client closes the connection
    while (True):
        global s1, s2, s3
        global s1_alive, s2_alive, s3_alive
        global s1_messenger, s2_messenger, s3_messenger
        global client_num
        global request_num
    
        # Bundle all server variables
        server_list = [s1, s2, s3]
        server_status_list = [s1_alive, s2_alive, s3_alive]
        server_messenger_list = [s1_messenger, s2_messenger, s3_messenger]

        # Repair the server connections
        vals = repair_connections(server_list, server_status_list, server_messenger_list)
        server_list, server_status_list, server_status_list = vals

        # Update server variables
        s1, s2, s3 = server_list
        s1_alive, s2_alive, s3_alive = server_status_list
        s1_messenger, s2_messenger, s3_messenger = server_messenger_list

        # Get user input
        attack_value = input("What is your next attack?\n")

        # Check if user requested to exit
        if (attack_value in ['exit', 'close', 'quit']):
            print("INFO: Closing connection")
            if s1_alive:
                s1.close()
            if s2_alive:
                s2.close()
            if s3_alive:
                s3.close()
            break

        # Check user input format
        if (attack_value.isdecimal() == False):
            print("ERROR: Input must be a valid integer")
            continue

        # Send the attack to the server
        request_num = request_num + 1
        to_be_receive.append(request_num)
        if s1_alive:
            try:
                s1_messenger.send(f"(Req#{request_num}) {attack_value}")
            except Exception:
                s1_alive = 0
        if s2_alive:
            try:
                #IN PASSIVE REPLICATION, DO NOT SEND TO S2
                pass
                #s2_messenger.send(f"(Req#{request_num}) {attack_value}")
            except Exception:
                s2_alive = 0
        if s3_alive:
            try:
                #IN PASSIVE REPLICATION, DO NOT SEND TO S3
                pass
                #s3_messenger.send(f"(Req#{request_num}) {attack_value}")
            except Exception:
                s3_alive = 0

        # Process the servers responses
        t1 = threading.Thread(target=listen2server,
                              args=(s1_alive, s1_messenger, s1),
                              daemon=True)
        #IN PASSIVE REPLICATION, DO NOT SEND TO S2 OR S3
        #t2 = threading.Thread(target=listen2server,
        #                      args=(s2_alive, s2_messenger, s2),
        #                      daemon=True)
        #t3 = threading.Thread(target=listen2server,
        #                      args=(s3_alive, s3_messenger, s3),
        #                      daemon=True)
        t1.start()

        #Wait for a little bit to get the response before prompting the user
        #again.
        time.sleep(0.010)

        #IN PASSIVE REPLICATION, DO NOT SEND TO S2 OR S3
        #t2.start()
        #t3.start()

if __name__ == '__main__':
    # Flag to mark whether server is available
    s1_alive = 1
    s2_alive = 1
    s3_alive = 1

    # Parse client number from CLI
    if len(sys.argv) < 2:
        raise ValueError("No Client Number Provided!")
    
    if len(sys.argv) > 2:
        raise ValueError("Too Many CLI Arguments!")

    client_num = int(sys.argv[1])

    # Open the connection to the server.
    s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    try:
        s1.connect((HOST, ports[f"S1_LISTEN"]))
    except Exception as e:
        s1_alive = 0
    try:
        s2.connect((HOST, ports[f"S2_LISTEN"]))
    except Exception as e:
        s2_alive = 0
    try:
        s3.connect((HOST, ports[f"S3_LISTEN"]))
    except Exception as e:
        s3_alive = 0

    # Setup logger
    logger = Logger()
    s1_messenger = Messenger(s1, f'C{client_num}', 'S1', logger)
    s2_messenger = Messenger(s2, f'C{client_num}', 'S2', logger)
    s3_messenger = Messenger(s3, f'C{client_num}', 'S3', logger)

    # Main Loop
    main()

    if s1_alive:
        s1.close()
    if s2_alive:
        s2.close()
    if s3_alive:
        s3.close()



