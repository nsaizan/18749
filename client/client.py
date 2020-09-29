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
sys.path.append("..")

# Custom imports
from helper import Logger
from helper import Messenger

# # # # # # # # # # # # #
# HOST & PORT SETTINGS  #
# # # # # # # # # # # # #

HOST = ''    # Accept connections on any IPv4 interface
PORT = 36337

# # # # # 
# MAIN  #
# # # # #
# Open the top-level listening socket.
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

    # Connect to the server
    s.connect((HOST, PORT))

    # Setup logger
    logger = Logger()
    messenger = Messenger(s, f'C{1}', 'S1', logger)

    message_count = 0

    # Run until client closes the connection
    while(True):
        # Get user input
        attack_value = input("What is your next attack? ")

        # Check if user requested to exit
        if(attack_value in ['exit','close','quit']):
            print("INFO: Closing connection")
            s.close()
            break

        # Check user input format
        if(attack_value.isdecimal() == False):
            print("ERROR: Input must be a valid integer")
            continue
            
        # Send and log the attack
        messenger.send(attack_value)

        # Wait to receive a reply (will be logged automatically) 
        while(not (messenger.recv(s, 1024))):
            pass
        
        
    s.close()

        
        
