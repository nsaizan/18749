#
#    File: Server Application
#  Author: aquinn, nsaizan, ranz2
#   Group: TheEnemy'sGateIsDown
#    Date: 9/14/2020
#
# Main code for our detector.

import socket
import threading
import time
import sys
sys.path.append("..")

# Custom imports
from helper import Logger
from helper import Messenger
from server.server import HEARTBEAT_FREQ_DEFAULT

# # # # # # # # # # # # #
# LFD HOST & PORT SETTINGS  #
# # # # # # # # # # # # #
LFD_HOST = '127.0.0.1' # Local Fault Detector should be on this machine.
LFD_PORT = 36338

TIMEOUT = 5 * HEARTBEAT_FREQ_DEFAULT # How long in seconds*Hz it takes to timeout

logger = Logger()

# # # # # # # # # # # # #
# THREAD FUNCTION DEFNS #
# # # # # # # # # # # # #
# Function to serve a single server.
def serve_server(conn, addr, socket):
    watchdog = TIMEOUT
    messenger = Messenger(None, '', '', logger)
    while True:
        # Wait for the server to send heartbeat msg.
        msg = messenger.recv(conn, 20)
        
        if msg:
            watchdog = TIMEOUT
            # TODO reset countdown to timeout
        else:
            watchdog -= 1
            if (watchdog == 0):
                messenger.error("Heartbeat timeout!")

        time.sleep(1/HEARTBEAT_FREQ_DEFAULT)


# # # # #
# MAIN  #
# # # # #
# Open the top-level listening socket.
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # Bind to the network port specified at top.
    s.bind((LFD_HOST, LFD_PORT))

    # This should be a listening port.
    s.listen()

    # Flavor Text
    print("\nThis is the fault detector interface.")
    print(" Should continue receiving heartbeat signal from server.")
    # Run forever
    while True:
        # Wait (blocking) for connections.
        conn, addr = s.accept()

        # Start a new thread to service the server.
        server = threading.Thread(target=serve_server, args=(conn, addr, s))
        server.start()
