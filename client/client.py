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
from ports  import HOST
from ports  import ports

# # # # # # # # # # # # #
# HOST & PORT SETTINGS  #
# # # # # # # # # # # # #

if __name__ == '__main__':

    # Parse client number from CLI
    if len(sys.argv) < 2:
        raise ValueError("No Client Number Provided!")
    
    if len(sys.argv) > 2:
        raise ValueError("Too Many CLI Arguments!")
    
    client_num = int(sys.argv[1])

    request_num = 0

    # Open the connection to the server.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        # Connect to the server
        s.connect((HOST, ports["S1_LISTENING"]))

        # Setup logger
        logger = Logger()
        messenger = Messenger(s, f'C{client_num}', 'S1', logger)

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
            request_num = request_num + 1
            messenger.send(f"(Req#{request_num}) {attack_value}")

            # Wait to receive a reply (will be logged automatically) 
            while(not (messenger.recv(s, 1024))):
                pass
            
            
        s.close()
