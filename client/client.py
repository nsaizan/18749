#
#    File: Client Application
#  Author: aquinn, nsaizan, ranz2
#   Group: TheEnemy'sGateIsDown
#    Date: 9/14/2020
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
    request_num = 0

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
    if s1_alive:
        messenger1 = Messenger(s1, f'C{client_num}', 'S1', logger)
    if s2_alive:
        messenger2 = Messenger(s2, f'C{client_num}', 'S2', logger)
    if s3_alive:
        messenger3 = Messenger(s3, f'C{client_num}', 'S3', logger)

    # Run until client closes the connection
    while (True):
        # Get user input
        attack_value = input("What is your next attack? ")

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

        # Send and log the attack
        request_num = request_num + 1
        to_be_receive.append(request_num)
        if s1_alive:
            try:
                messenger1.send(f"(Req#{request_num}) {attack_value}")
            except Exception as e:
                s1_alive = 0
                pass
        if s2_alive:
            try:
                messenger2.send(f"(Req#{request_num}) {attack_value}")
            except Exception as e:
                s2_alive = 0
                pass
        if s3_alive:
            try:
                messenger3.send(f"(Req#{request_num}) {attack_value}")
            except Exception as e:
                s3_alive = 0
                pass

        # Wait to receive a reply (will be logged automatically)
        # while (not (messenger.recv(s))):
        # pass

        if s1_alive:
            try:
                msg1 = messenger1.recv(s1)
                if msg1:
                    try:
                        req_num = int(msg1.split(')')[0].split('#')[1])
                    except (IndexError, ValueError) as e:
                        logger.error('Bad message from client.')
                        continue
                    if req_num in to_be_receive:
                        to_be_receive.remove(req_num)
                    else:
                        print("discard duplicated info.")
                else:
                    continue
            except Exception as e:
                s1_alive = 0
                pass

        if s2_alive:
            try:
                msg2 = messenger2.recv(s2)
                if msg2:
                    try:
                        req_num = int(msg2.split(')')[0].split('#')[1])
                    except (IndexError, ValueError) as e:
                        logger.error('Bad message from client.')
                        continue
                    if req_num in to_be_receive:
                        to_be_receive.remove(req_num)
                    else:
                        print("discard duplicated info.")
                else:
                    continue
            except Exception as e:
                s2_alive = 0
                pass

        if s3_alive:
            try:
                msg3 = messenger3.recv(s3)
                if msg2:
                    try:
                        req_num = int(msg3.split(')')[0].split('#')[1])
                    except (IndexError, ValueError) as e:
                        logger.error('Bad message from client.')
                        continue
                    if req_num in to_be_receive:
                        to_be_receive.remove(req_num)
                    else:
                        print("discard duplicated info.")
                else:
                    continue
            except Exception as e:
                s3_alive = 0
                pass

    if s1_alive:
        s1.close()
    if s2_alive:
        s2.close()
    if s3_alive:
        s3.close()



