#
#    File: Server Application
#  Author: aquinn, nsaizan, ranz2
#   Group: TheEnemy'sGateIsDown
#    Date: 9/14/2020
#
# Main code for our detector.

import socket
import threading
import sys
import time

# # # # # # # # # # # # #
# LFD HOST & PORT SETTINGS  #
# # # # # # # # # # # # #
HOST = '' # Local Fault Detector should be on the same machine as server
PORT = 36337
LFD_R_PORT = 36338 # Port for LFD to receive receipt


# # # # # # # # # # # # #
# THREAD FUNCTION DEFNS #
# # # # # # # # # # # # #
# Function to serve a single server.
def send_heartbeat(frequency):
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as heartbeat_socket:
            # Connect to the detector
            try:
                heartbeat_socket.connect((HOST, PORT))
                Flag_e = 1

                # TODO
                # Now just send heartbeat to local detector, should send through each
                # replicated server later on

                msg = "HB from PORT: " + str(PORT)
                heartbeat_msg = msg.encode()

                while True:
                    heartbeat_socket.send(heartbeat_msg)
                    print(msg)
                    time.sleep(int(frequency))
            except Exception as e:
                if Flag_e:
                    print("The server crashed.")
                    Flag_e = 0
                heartbeat_socket.close()


# # # # #
# MAIN  #
# # # # #
# Parse heartbeat frequency from the input
if len(sys.argv) < 2:
    raise ValueError("No Heartbeat Frequency Provided!")

if len(sys.argv) > 2:
    raise ValueError("Too Many CLI Arguments!")

freq = sys.argv[1]


heartbeat = threading.Thread(target=send_heartbeat, args = (freq,))
heartbeat.start()